"""
Developer 2 — Place Provider abstraction.

Developer 1 owns the places system (Google Places API via app/api/places.py and
app/services/maps/places_service.py).  Developer 2 must NOT duplicate that work.

This module defines:
  - PlaceInfo: the minimal data structure Developer 2 needs from a place.
  - PlaceProvider: the abstract interface.
  - GooglePlaceProvider: calls Developer 1's PlacesService internally.
  - MockPlaceProvider: DEVELOPMENT-ONLY stub used in tests without a live API key.

Usage in production:
    from app.gamification.place_provider import get_place_provider
    provider = get_place_provider()
    place = await provider.get_place("ChIJ...")

Integration note:
    Developer 1's PlacesService returns raw Google Places API payloads.
    GooglePlaceProvider extracts only the fields Developer 2 needs and adds
    verification_radius from settings (place-specific radii can be added later
    by Developer 1 via a database column or config map).
"""
from __future__ import annotations

import abc
from dataclasses import dataclass
from typing import Optional

from fastapi import HTTPException

from app.config import settings


@dataclass(frozen=True)
class PlaceInfo:
    place_id: str
    name: str
    latitude: float
    longitude: float
    verification_radius: float  # metres


class PlaceProvider(abc.ABC):
    """Abstract interface for obtaining place coordinates and verification radius."""

    @abc.abstractmethod
    async def get_place(self, place_id: str) -> PlaceInfo:
        """Return PlaceInfo or raise HTTPException(404) if not found."""


class GooglePlaceProvider(PlaceProvider):
    """
    Delegates to Developer 1's PlacesService.
    Uses place-specific verification_radius when available in the Google payload,
    otherwise falls back to settings.DEFAULT_VISIT_RADIUS_METERS.
    """

    def __init__(self) -> None:
        from app.services.maps.places_service import PlacesService
        self._svc = PlacesService()

    async def get_place(self, place_id: str) -> PlaceInfo:
        try:
            data = await self._svc.details(place_id)
        except HTTPException as exc:
            if exc.status_code in (404, 400):
                raise HTTPException(
                    status_code=404,
                    detail={"code": "PLACE_NOT_FOUND", "message": f"Place '{place_id}' not found"},
                ) from exc
            raise

        location = data.get("location") or {}
        lat = location.get("latitude")
        lng = location.get("longitude")

        if lat is None or lng is None:
            raise HTTPException(
                status_code=404,
                detail={"code": "PLACE_NOT_FOUND", "message": f"Place '{place_id}' has no usable coordinates"},
            )

        name = (data.get("displayName") or {}).get("text") or place_id
        radius = float(settings.DEFAULT_VISIT_RADIUS_METERS)

        return PlaceInfo(
            place_id=place_id,
            name=name,
            latitude=float(lat),
            longitude=float(lng),
            verification_radius=radius,
        )


class MockPlaceProvider(PlaceProvider):
    """
    DEVELOPMENT AUTH STUB — for tests and local development WITHOUT a Google API key.

    Pre-seeded with a handful of Indian tourist places.
    Additional places can be registered via register().
    """

    _BUILT_IN: dict[str, PlaceInfo] = {
        "PLACE-KONARK": PlaceInfo(
            place_id="PLACE-KONARK",
            name="Konark Sun Temple",
            latitude=19.8876,
            longitude=86.0945,
            verification_radius=150.0,
        ),
        "PLACE-TAJMAHAL": PlaceInfo(
            place_id="PLACE-TAJMAHAL",
            name="Taj Mahal",
            latitude=27.1751,
            longitude=78.0421,
            verification_radius=200.0,
        ),
        "PLACE-GOLDENTEMPLE": PlaceInfo(
            place_id="PLACE-GOLDENTEMPLE",
            name="Golden Temple",
            latitude=31.6200,
            longitude=74.8765,
            verification_radius=100.0,
        ),
        "PLACE-GATEWAY": PlaceInfo(
            place_id="PLACE-GATEWAY",
            name="Gateway of India",
            latitude=18.9220,
            longitude=72.8347,
            verification_radius=100.0,
        ),
    }

    def __init__(self) -> None:
        self._places: dict[str, PlaceInfo] = dict(self._BUILT_IN)

    def register(self, place: PlaceInfo) -> None:
        self._places[place.place_id] = place

    async def get_place(self, place_id: str) -> PlaceInfo:
        if place_id not in self._places:
            raise HTTPException(
                status_code=404,
                detail={"code": "PLACE_NOT_FOUND", "message": f"Place '{place_id}' not found"},
            )
        return self._places[place_id]


# ---------------------------------------------------------------------------
# Factory — returns the right provider based on environment / config
# ---------------------------------------------------------------------------

def get_place_provider() -> PlaceProvider:
    """
    Returns GooglePlaceProvider when GOOGLE_MAPS_API_KEY is set,
    otherwise returns MockPlaceProvider for development/testing.
    """
    if settings.GOOGLE_MAPS_API_KEY:
        return GooglePlaceProvider()
    return MockPlaceProvider()
