from datetime import date
from types import SimpleNamespace

from app.schemas import PlannerPreferences, PlannerRequest
from app.services.planner import generate_itinerary


def _request(**overrides):
    data = {
        "start_location": {"latitude": 19.8, "longitude": 85.8},
        "destinations": ["p1", "p2"],
        "available_hours": 8,
        "days": 1,
        "start_time": "08:00",
        "start_date": date(2026, 10, 2),
        "visit_duration_minutes": 90,
        "return_to_start": True,
        "preferences": PlannerPreferences(),
    }
    data.update(overrides)
    return PlannerRequest(**data)


def _matrix():
    # start=0, p1=1, p2=2
    def leg(a, b, minutes):
        return {"originIndex": a, "destinationIndex": b, "status": {"code": 0}, "condition": "ROUTE_EXISTS", "duration": f"{minutes * 60}s", "distanceMeters": minutes * 1000}
    return [leg(a, b, 20 if a != b else 0) for a in range(3) for b in range(3)]


def _place(pid, name, periods=None):
    return {"id": pid, "displayName": {"text": name}, "types": ["tourist_attraction"], "location": {"latitude": 19.8, "longitude": 85.8}, "regularOpeningHours": {"periods": periods} if periods else None}


def test_planner_uses_route_times_and_return_leg():
    result = generate_itinerary([_place("p1", "A"), _place("p2", "B")], _matrix(), {"p1": [], "p2": []}, _request())
    assert result["planning_summary"]["scheduled_destinations"] == 2
    activities = result["days"][0]["activities"]
    assert activities[0]["travel_minutes"] == 20
    assert activities[-1]["place_id"] == "__start__"
    assert activities[-1]["travel_minutes"] == 20


def test_planner_respects_opening_hours():
    # Friday is Google day 5. Open 10:00-12:00, so an 08:00 arrival waits until 10.
    periods = [{"open": {"day": 5, "time": "1000"}, "close": {"day": 5, "time": "1200"}}]
    result = generate_itinerary([_place("p1", "A", periods)], _matrix(), {"p1": []}, _request(destinations=["p1"]))
    activity = result["days"][0]["activities"][0]
    assert activity["arrival"] == "10:00"
    assert activity["waiting_minutes"] == 100


def test_planner_skips_closed_place_instead_of_scheduling_it():
    periods = [{"open": {"day": 5, "time": "1400"}, "close": {"day": 5, "time": "1500"}}]
    result = generate_itinerary([_place("p1", "A", periods)], _matrix(), {"p1": []}, _request(destinations=["p1"]))
    assert result["planning_summary"]["scheduled_destinations"] == 0
    assert result["skipped"][0]["place_id"] == "p1"
