from datetime import datetime
from types import SimpleNamespace

from app.services.crowd.collector import normalize_crowd_level
from app.services.crowd.predictor import best_time_slots, predict_from_observations


def test_normalize():
    assert normalize_crowd_level("very low") == "VERY_LOW"


def test_prediction():
    obs = [
        SimpleNamespace(timestamp=datetime(2026, 10, 2, 8), crowd_level="LOW", confidence=0.9),
        SimpleNamespace(timestamp=datetime(2026, 10, 2, 8), crowd_level="LOW", confidence=0.8),
    ]
    result = predict_from_observations(obs, 8)
    assert result["predicted_level"] == "LOW"


def test_best_time():
    obs = [
        SimpleNamespace(timestamp=datetime(2026, 10, 2, 8), crowd_level="LOW", confidence=0.9),
        SimpleNamespace(timestamp=datetime(2026, 10, 2, 12), crowd_level="HIGH", confidence=0.9),
    ]
    slots = best_time_slots(obs, (8, 12))
    assert slots[0]["hour"] == 8
