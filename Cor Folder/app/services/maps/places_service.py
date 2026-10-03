import httpx
from fastapi import HTTPException

from app.config import settings
from app.services.maps.base import request_with_retries

PLACES_BASE = "https://places.googleapis.com/v1"


class PlacesService:
    def __init__(self):
        self.api_key = settings.GOOGLE_MAPS_API_KEY

    def _headers(self, field_mask: str):
        if not self.api_key or self.api_key.startswith("your_"):
            raise HTTPException(status_code=503, detail={"code": "GOOGLE_MAPS_NOT_CONFIGURED", "message": "Google Maps integration is not configured"})
        return {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": field_mask,
        }

    async def search_text(self, query: str, max_result_count: int = 10):
        url = f"{PLACES_BASE}/places:searchText"
        body = {"textQuery": query.strip(), "maxResultCount": max_result_count}
        mask = (
            "places.id,places.displayName,places.formattedAddress,places.location,"
            "places.primaryType,places.types,places.googleMapsUri"
        )
        async with httpx.AsyncClient(timeout=settings.GOOGLE_TIMEOUT_SECONDS) as client:
            r = await request_with_retries(client, "POST", url, headers=self._headers(mask), json_body=body, retries=settings.GOOGLE_RETRIES, service="google_places")
        return r.json()

    async def nearby_search(self, lat: float, lng: float, radius_meters: int, types: list[str]):
        url = f"{PLACES_BASE}/places:searchNearby"
        body = {
            "locationRestriction": {"circle": {"center": {"latitude": lat, "longitude": lng}, "radius": radius_meters}},
            "maxResultCount": 20,
        }
        if types:
            body["includedTypes"] = types
        mask = (
            "places.id,places.displayName,places.formattedAddress,places.location,"
            "places.primaryType,places.types,places.googleMapsUri"
        )
        async with httpx.AsyncClient(timeout=settings.GOOGLE_TIMEOUT_SECONDS) as client:
            r = await request_with_retries(client, "POST", url, headers=self._headers(mask), json_body=body, retries=settings.GOOGLE_RETRIES, service="google_places")
        return r.json()

    async def details(self, place_id: str):
        url = f"{PLACES_BASE}/places/{place_id}"
        mask = (
            "id,displayName,formattedAddress,location,types,primaryType,"
            "regularOpeningHours,currentOpeningHours,googleMapsUri,websiteUri,"
            "rating,userRatingCount,photos"
        )
        async with httpx.AsyncClient(timeout=settings.GOOGLE_TIMEOUT_SECONDS) as client:
            r = await request_with_retries(client, "GET", url, headers=self._headers(mask), retries=settings.GOOGLE_RETRIES, service="google_places")
        return r.json()
