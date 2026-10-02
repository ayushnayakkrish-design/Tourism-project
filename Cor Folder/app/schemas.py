from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Coordinates(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class PlaceSearchResponse(BaseModel):
    places: list[dict]


class NearbyRequest(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    radius_meters: int = Field(default=5000, ge=1, le=50000)
    included_types: list[str] = Field(default_factory=list, max_length=20)


class CrowdObservationCreate(BaseModel):
    place_id: str = Field(min_length=1, max_length=255)
    timestamp: Optional[datetime] = None
    crowd_level: str = Field(min_length=1, max_length=30)
    source: str = Field(default="manual", min_length=1, max_length=100)
    confidence: float = Field(default=0.7, ge=0, le=1)


class CrowdObservationOut(CrowdObservationCreate):
    id: int


class PlannerPreferences(BaseModel):
    temples: bool = False
    nature: bool = False
    food: bool = False
    beaches: bool = False
    culture: bool = False
    shopping: bool = False


class PlannerRequest(BaseModel):
    start_location: Coordinates
    destinations: list[str] = Field(min_length=1, max_length=12)
    available_hours: float = Field(default=8, gt=0, le=24)
    days: int = Field(default=1, ge=1, le=14)
    start_time: str = "08:00"
    start_date: date = Field(default_factory=date.today)
    visit_duration_minutes: int = Field(default=90, ge=15, le=480)
    return_to_start: bool = True
    preferences: PlannerPreferences = Field(default_factory=PlannerPreferences)

    @field_validator("start_time")
    @classmethod
    def validate_start_time(cls, value: str) -> str:
        import re
        if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", value):
            raise ValueError("start_time must use HH:MM in 24-hour format")
        return value

    @field_validator("destinations")
    @classmethod
    def validate_destinations(cls, value: list[str]) -> list[str]:
        cleaned = [x.strip() for x in value if x.strip()]
        if len(cleaned) != len(set(cleaned)):
            raise ValueError("destinations must not contain duplicates")
        if not cleaned:
            raise ValueError("at least one destination is required")
        return cleaned


class SeasonRequest(BaseModel):
    place_id: str = Field(min_length=1, max_length=255)
    month: int = Field(ge=1, le=12)


class SeasonProfileCreate(BaseModel):
    place_id: str = Field(min_length=1, max_length=255)
    month: int = Field(ge=1, le=12)
    weather_score: float = Field(ge=0, le=100)
    crowd_score: float = Field(ge=0, le=100)
    festival_score: float = Field(ge=0, le=100)
    accessibility_score: float = Field(ge=0, le=100)
    reason: str = Field(default="", max_length=2000)


class ItineraryExplanationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    itinerary: dict = Field(min_length=1)
