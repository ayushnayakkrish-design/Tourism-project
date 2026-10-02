from __future__ import annotations

from datetime import date, datetime, timedelta
from math import inf

from app.services.crowd.predictor import predict_from_observations
from app.services.crowd.scoring import crowd_score


def parse_time(value: str) -> datetime:
    return datetime.strptime(value, "%H:%M")


def format_time(dt: datetime) -> str:
    return dt.strftime("%H:%M")


def preference_match(place: dict, preferences) -> int:
    types = set(place.get("types", []))
    score = 0
    if preferences.temples and ("hindu_temple" in types or "tourist_attraction" in types):
        score += 3
    if preferences.nature and any(x in types for x in ["park", "national_park", "natural_feature", "beach"]):
        score += 3
    if preferences.food and ("restaurant" in types or "cafe" in types):
        score += 3
    if preferences.beaches and "beach" in types:
        score += 3
    if preferences.culture and ("museum" in types or "art_gallery" in types):
        score += 3
    if preferences.shopping and ("shopping_mall" in types or "market" in types):
        score += 3
    return score


def duration_to_minutes(value: str | None) -> int | None:
    if not value:
        return None
    try:
        return max(1, round(float(value.rstrip("s")) / 60))
    except (TypeError, ValueError):
        return None


def _matrix_lookup(route_matrix: list[dict], origin_index: int, destination_index: int) -> dict | None:
    for item in route_matrix:
        if item.get("originIndex") == origin_index and item.get("destinationIndex") == destination_index:
            status = item.get("status")
            if isinstance(status, dict):
                if status.get("code", 0) != 0:
                    return None
            elif status not in (None, "OK"):
                return None
            if item.get("condition") not in (None, "ROUTE_EXISTS"):
                return None
            return item
    return None


def _period_minutes(value: str | None) -> int | None:
    if not value:
        return None
    try:
        return int(value[:2]) * 60 + int(value[2:4])
    except (TypeError, ValueError):
        return None


def _opening_windows(place: dict, weekday: int) -> list[tuple[int, int]]:
    # Google uses Sunday=0 ... Saturday=6; Python uses Monday=0 ... Sunday=6.
    google_day = (weekday + 1) % 7
    hours = place.get("regularOpeningHours") or {}
    periods = hours.get("periods") or []
    windows: list[tuple[int, int]] = []
    for period in periods:
        open_data = period.get("open") or {}
        close_data = period.get("close") or {}
        if open_data.get("day") != google_day:
            continue
        start = _period_minutes(open_data.get("time"))
        if start is None:
            start = 0
        end = _period_minutes(close_data.get("time"))
        if end is None:
            end = 24 * 60
        if end <= start:
            end = 24 * 60
        windows.append((start, end))
    return windows


def _fit_visit(place: dict, arrival: datetime, visit_minutes: int, start_date: date) -> datetime | None:
    # If opening hours are absent, do not invent restrictions.
    hours = place.get("regularOpeningHours")
    if not hours or not hours.get("periods"):
        return arrival
    windows = _opening_windows(place, arrival.weekday())
    if not windows:
        return None
    arrival_minutes = arrival.hour * 60 + arrival.minute
    for start, end in windows:
        candidate = max(arrival_minutes, start)
        if candidate + visit_minutes <= end:
            return arrival.replace(hour=candidate // 60, minute=candidate % 60, second=0, microsecond=0)
    return None


def _select_route_order(candidates: list[dict], matrix: list[dict], return_to_start: bool) -> list[dict]:
    """Greedy route construction: minimize travel first, then preference/crowd value.

    Node 0 is the start location. Candidate nodes are 1..N.
    """
    if not candidates:
        return []
    remaining = {x["node_index"]: x for x in candidates}
    current = 0
    ordered: list[dict] = []
    while remaining:
        best = None
        for node, candidate in remaining.items():
            leg = _matrix_lookup(matrix, current, node)
            if leg is None:
                continue
            travel = duration_to_minutes(leg.get("duration"))
            if travel is None:
                continue
            # Crowd and preferences influence ties/near-ties without overriding route feasibility.
            value = candidate["preference_score"] * 10 + candidate["crowd_score"]
            key = (travel, -value)
            if best is None or key < best[0]:
                best = (key, node, candidate)
        if best is None:
            break
        _, node, candidate = best
        ordered.append(candidate)
        remaining.pop(node)
        current = node

    if return_to_start and ordered:
        # Return time is calculated later from the final node to start.
        pass
    return ordered


def generate_itinerary(places, route_matrix, observations_by_place, request):
    by_id = {place.get("id"): place for place in places if place.get("id")}
    candidates = []
    for index, place in enumerate(places, start=1):
        pid = place["id"]
        observations = observations_by_place.get(pid, [])
        prediction = predict_from_observations(observations, 9)
        candidates.append({
            "node_index": index,
            "place": place,
            "prediction": prediction,
            "preference_score": preference_match(place, request.preferences),
            "crowd_score": crowd_score(prediction["predicted_level"]),
        })

    ordered = _select_route_order(candidates, route_matrix, request.return_to_start)
    days = []
    max_minutes = int(request.available_hours * 60)
    day_number = 1
    cursor = parse_time(request.start_time).replace(
        year=request.start_date.year, month=request.start_date.month, day=request.start_date.day
    )
    current_day: list[dict] = []
    used = 0
    current_node = 0
    skipped = []

    for candidate in ordered:
        place = candidate["place"]
        node = candidate["node_index"]
        leg = _matrix_lookup(route_matrix, current_node, node)
        if leg is None:
            skipped.append({"place_id": place["id"], "reason": "No route found from the previous stop"})
            continue
        travel_minutes = duration_to_minutes(leg.get("duration"))
        if travel_minutes is None:
            skipped.append({"place_id": place["id"], "reason": "Route duration unavailable"})
            continue

        arrival = cursor + timedelta(minutes=travel_minutes)
        visit_start = _fit_visit(place, arrival, request.visit_duration_minutes, request.start_date)
        if visit_start is None:
            skipped.append({"place_id": place["id"], "reason": "Closed on the planned day/time"})
            continue
        opening_wait = max(0, int((visit_start - arrival).total_seconds() / 60))
        total_needed = travel_minutes + opening_wait + request.visit_duration_minutes

        if used + total_needed > max_minutes:
            if current_day:
                days.append({"day": day_number, "date": cursor.date().isoformat(), "activities": current_day})
                day_number += 1
                if day_number > request.days:
                    skipped.append({"place_id": place["id"], "reason": "Not enough remaining itinerary time"})
                    break
                cursor = parse_time(request.start_time).replace(
                    year=request.start_date.year, month=request.start_date.month, day=request.start_date.day
                ) + timedelta(days=day_number - 1)
                current_day = []
                used = 0
                current_node = 0
                # Recompute route from start for the new day.
                leg = _matrix_lookup(route_matrix, 0, node)
                if leg is None:
                    skipped.append({"place_id": place["id"], "reason": "No route found from start location"})
                    continue
                travel_minutes = duration_to_minutes(leg.get("duration")) or 0
                arrival = cursor + timedelta(minutes=travel_minutes)
                visit_start = _fit_visit(place, arrival, request.visit_duration_minutes, cursor.date())
                if visit_start is None:
                    skipped.append({"place_id": place["id"], "reason": "Closed on the planned day/time"})
                    continue
                opening_wait = max(0, int((visit_start - arrival).total_seconds() / 60))
                total_needed = travel_minutes + opening_wait + request.visit_duration_minutes
            else:
                skipped.append({"place_id": place["id"], "reason": "Visit duration plus travel exceeds available daily time"})
                continue

        arrival = cursor + timedelta(minutes=travel_minutes)
        visit_start = _fit_visit(place, arrival, request.visit_duration_minutes, cursor.date()) or arrival
        opening_wait = max(0, int((visit_start - arrival).total_seconds() / 60))
        scheduled_prediction = predict_from_observations(
            observations_by_place.get(place["id"], []),
            visit_start.hour,
            visit_start.weekday(),
        )
        visit_end = visit_start + timedelta(minutes=request.visit_duration_minutes)
        used += travel_minutes + opening_wait + request.visit_duration_minutes
        cursor = visit_end
        current_node = node
        current_day.append({
            "place": place.get("displayName", {}).get("text", place["id"]),
            "place_id": place["id"],
            "arrival": format_time(visit_start),
            "duration": request.visit_duration_minutes,
            "travel_minutes": travel_minutes,
            "waiting_minutes": opening_wait,
            "crowd": scheduled_prediction["predicted_level"],
            "crowd_confidence": scheduled_prediction["confidence"],
            "reason": "Selected using route feasibility, user preferences, and crowd score.",
        })

    if current_day and day_number <= request.days:
        if request.return_to_start and current_node != 0:
            return_leg = _matrix_lookup(route_matrix, current_node, 0)
            return_minutes = duration_to_minutes(return_leg.get("duration")) if return_leg else None
            if return_minutes is not None and used + return_minutes <= max_minutes:
                used += return_minutes
                cursor += timedelta(minutes=return_minutes)
                current_day.append({
                    "place": "Start location",
                    "place_id": "__start__",
                    "arrival": format_time(cursor),
                    "duration": 0,
                    "travel_minutes": return_minutes,
                    "waiting_minutes": 0,
                    "crowd": None,
                    "crowd_confidence": None,
                    "reason": "Return leg calculated from Google Routes matrix.",
                })
            elif return_minutes is not None:
                skipped.append({"place_id": "__start__", "reason": "Return trip exceeds remaining daily time"})
        days.append({"day": day_number, "date": cursor.date().isoformat(), "activities": current_day})

    return {
        "days": days,
        "route_matrix": route_matrix,
        "skipped": skipped,
        "planning_summary": {
            "requested_destinations": len(request.destinations),
            "scheduled_destinations": sum(len([a for a in d["activities"] if a["place_id"] != "__start__"]) for d in days),
            "skipped_destinations": len([x for x in skipped if x["place_id"] != "__start__"]),
            "return_to_start": request.return_to_start,
        },
    }
