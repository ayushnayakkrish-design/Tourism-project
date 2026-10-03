import json

import httpx
from fastapi import HTTPException

from app.config import settings
from app.services.maps.base import request_with_retries

ROUTES_BASE = "https://routes.googleapis.com"


class RoutesService:
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

    async def compute_route(self, origin: dict, destination: dict, intermediates=None):
        url = f"{ROUTES_BASE}/directions/v2:computeRoutes"
        body = {
            "origin": {"location": {"latLng": origin}},
            "destination": {"location": {"latLng": destination}},
            "travelMode": "DRIVE",
            "routingPreference": "TRAFFIC_AWARE",
            "computeAlternativeRoutes": False,
            "units": "METRIC",
        }
        if intermediates:
            body["intermediates"] = [{"location": {"latLng": x}} for x in intermediates]
        mask = "routes.duration,routes.distanceMeters,routes.polyline.encodedPolyline"
        async with httpx.AsyncClient(timeout=settings.GOOGLE_TIMEOUT_SECONDS) as client:
            r = await request_with_retries(client, "POST", url, headers=self._headers(mask), json_body=body, retries=settings.GOOGLE_RETRIES, service="google_routes")
        return r.json()

    async def compute_matrix(self, origins: list[dict], destinations: list[dict]):
        if not origins or not destinations:
            raise HTTPException(status_code=422, detail={"code": "EMPTY_ROUTE_MATRIX", "message": "origins and destinations must not be empty"})
        if len(origins) * len(destinations) > 625:
            raise HTTPException(status_code=422, detail={"code": "ROUTE_MATRIX_TOO_LARGE", "message": "Route matrix is limited to 625 origin-destination pairs"})

        url = f"{ROUTES_BASE}/distanceMatrix/v2:computeRouteMatrix"
        body = {
            "origins": [{"waypoint": {"location": {"latLng": x}}} for x in origins],
            "destinations": [{"waypoint": {"location": {"latLng": x}}} for x in destinations],
            "travelMode": "DRIVE",
            "routingPreference": "TRAFFIC_AWARE",
        }
        mask = "originIndex,destinationIndex,status,condition,distanceMeters,duration"
        async with httpx.AsyncClient(timeout=max(settings.GOOGLE_TIMEOUT_SECONDS, 30)) as client:
            r = await request_with_retries(client, "POST", url, headers=self._headers(mask), json_body=body, retries=settings.GOOGLE_RETRIES, service="google_routes")

        text = r.text.strip()
        if not text:
            return []
        try:
            parsed = r.json()
            if isinstance(parsed, list):
                return parsed
        except ValueError:
            pass

        result = []
        for line in text.splitlines():
            line = line.strip()
            if line:
                try:
                    result.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise HTTPException(status_code=502, detail={"code": "GOOGLE_ROUTES_INVALID_RESPONSE", "message": "Google returned an invalid route matrix response"}) from exc
        return result
