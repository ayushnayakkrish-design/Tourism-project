from fastapi import APIRouter, Query

from app.schemas import NearbyRequest
from app.services.maps.places_service import PlacesService
from app.services.maps.geocoding_service import GeocodingService

router = APIRouter()
service = PlacesService()
geocoding_service = GeocodingService()


def normalize_place(p: dict) -> dict:
    return {
        "place_id": p.get("id"),
        "name": p.get("displayName", {}).get("text"),
        "latitude": p.get("location", {}).get("latitude"),
        "longitude": p.get("location", {}).get("longitude"),
        "type": p.get("primaryType"),
        "types": p.get("types", []),
        "address": p.get("formattedAddress"),
        "map_url": p.get("googleMapsUri"),
    }


@router.get("/search")
async def search_places(q: str = Query(min_length=2, max_length=200), max_results: int = Query(10, ge=1, le=20)):
    data = await service.search_text(q, max_results)
    return {"places": [normalize_place(p) for p in data.get("places", [])]}


@router.get("/geocode")
async def geocode(address: str = Query(min_length=2, max_length=300)):
    return await geocoding_service.geocode(address)


@router.get("/{place_id}")
async def place_details(place_id: str):
    data = await service.details(place_id)
    return {
        "place_id": data.get("id"),
        "name": data.get("displayName", {}).get("text"),
        "description": data.get("editorialSummary", {}).get("text") if data.get("editorialSummary") else None,
        "location": data.get("location"),
        "opening_hours": data.get("regularOpeningHours"),
        "current_opening_hours": data.get("currentOpeningHours"),
        "categories": data.get("types", []),
        "primary_type": data.get("primaryType"),
        "rating": data.get("rating"),
        "user_rating_count": data.get("userRatingCount"),
        "website": data.get("websiteUri"),
        "map_query": data.get("googleMapsUri"),
        "photos": data.get("photos", []),
    }


@router.post("/nearby")
async def nearby_places(request: NearbyRequest):
    data = await service.nearby_search(request.latitude, request.longitude, request.radius_meters, request.included_types)
    return {"places": [normalize_place(p) for p in data.get("places", [])]}
