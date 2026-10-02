import pytest
from pydantic import ValidationError

from app.schemas import Coordinates, PlannerRequest


def test_coordinate_bounds():
    with pytest.raises(ValidationError):
        Coordinates(latitude=91, longitude=85)
    with pytest.raises(ValidationError):
        Coordinates(latitude=19, longitude=181)


def test_planner_time_and_duplicates_validation():
    with pytest.raises(ValidationError):
        PlannerRequest(start_location={"latitude": 19, "longitude": 85}, destinations=["a"], start_time="8:00")
    with pytest.raises(ValidationError):
        PlannerRequest(start_location={"latitude": 19, "longitude": 85}, destinations=["a", "a"])
