from collections import defaultdict
from datetime import datetime

LEVELS = ["VERY_LOW", "LOW", "MODERATE", "HIGH", "VERY_HIGH"]
LEVEL_SCORE = {name: i for i, name in enumerate(LEVELS)}


def predict_from_observations(observations, target_hour: int, target_weekday: int | None = None):
    if not observations:
        return {"predicted_level": "MODERATE", "confidence": 0.25, "sample_count": 0}

    exact = [obs for obs in observations if obs.timestamp.hour == target_hour]
    if target_weekday is not None:
        weekday_matches = [obs for obs in exact if obs.timestamp.weekday() == target_weekday]
        if weekday_matches:
            exact = weekday_matches
    buckets = exact or observations

    weighted_sum = 0.0
    weight_total = 0.0
    for obs in buckets:
        score = LEVEL_SCORE.get(str(obs.crowd_level).upper(), 2)
        recency_days = max(0, (datetime.now() - obs.timestamp.replace(tzinfo=None)).days)
        recency_weight = 1 / (1 + recency_days / 30)
        weight = max(0.05, float(obs.confidence)) * recency_weight
        weighted_sum += score * weight
        weight_total += weight

    weighted = weighted_sum / weight_total if weight_total else 2
    index = min(4, max(0, round(weighted)))
    confidence = min(0.95, 0.35 + 0.1 * len(buckets))
    if not exact:
        confidence = max(0.25, confidence - 0.15)

    return {
        "predicted_level": LEVELS[index],
        "confidence": round(confidence, 2),
        "sample_count": len(buckets),
        "target_hour": target_hour,
    }


def best_time_slots(observations, opening_hours=(8, 18)):
    result = []
    for hour in range(opening_hours[0], opening_hours[1] + 1):
        prediction = predict_from_observations(observations, hour)
        result.append({"hour": hour, **prediction})
    return sorted(result, key=lambda x: (LEVEL_SCORE[x["predicted_level"]], -x["confidence"]))
