import httpx
from fastapi import HTTPException

from app.config import settings
from app.services.maps.base import request_with_retries


class GeocodingService:
    BASE = "https://maps.googleapis.com/maps/api/geocode/json"

    async def geocode(self, address: str):
        if not settings.GOOGLE_MAPS_API_KEY or settings.GOOGLE_MAPS_API_KEY.startswith("your_"):
            raise HTTPException(status_code=503, detail={"code": "GOOGLE_MAPS_NOT_CONFIGURED", "message": "Google Maps integration is not configured"})
        params = {"address": address.strip(), "key": settings.GOOGLE_MAPS_API_KEY}
        headers = {"Accept": "application/json"}
        async with httpx.AsyncClient(timeout=settings.GOOGLE_TIMEOUT_SECONDS) as client:
            try:
                response = await client.get(self.BASE, params=params, headers=headers)
            except httpx.RequestError as exc:
                raise HTTPException(status_code=502, detail={"code": "GEOCODING_NETWORK_ERROR", "message": "Could not reach geocoding service"}) from exc
        if response.status_code >= 400:
            raise HTTPException(status_code=502, detail={"code": "GEOCODING_UPSTREAM_ERROR", "message": "Geocoding service request failed"})
        payload = response.json()
        if payload.get("status") not in {"OK", "ZERO_RESULTS"}:
            raise HTTPException(status_code=502, detail={"code": "GEOCODING_UPSTREAM_ERROR", "message": "Geocoding service returned an error"})
        return {
            "status": payload.get("status"),
            "results": [
                {
                    "formatted_address": x.get("formatted_address"),
                    "latitude": x.get("geometry", {}).get("location", {}).get("lat"),
                    "longitude": x.get("geometry", {}).get("location", {}).get("lng"),
                    "place_id": x.get("place_id"),
                    "types": x.get("types", []),
                }
                for x in payload.get("results", [])
            ],
        }
