from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import CrowdObservation
from app.schemas import ItineraryExplanationRequest, PlannerRequest
from app.services.ai_service import AIService
from app.services.maps.places_service import PlacesService
from app.services.maps.routes_service import RoutesService
from app.services.planner import generate_itinerary

router = APIRouter()
places_service = PlacesService()
routes_service = RoutesService()
ai_service = AIService()


@router.post("/generate")
async def generate(request: PlannerRequest, db: Session = Depends(get_db)):
    places = []
    observations_by_place = {}
    for place_id in request.destinations:
        detail = await places_service.details(place_id)
        if not detail.get("location"):
            continue
        places.append(detail)
        observations_by_place[place_id] = (
            db.query(CrowdObservation)
            .filter(CrowdObservation.place_id == place_id)
            .order_by(CrowdObservation.timestamp.desc())
            .limit(200)
            .all()
        )

    if not places:
        return {"days": [], "route_matrix": [], "skipped": [{"reason": "No destination has usable coordinates"}]}

    nodes = [request.start_location.model_dump()] + [
        {"latitude": p["location"]["latitude"], "longitude": p["location"]["longitude"]} for p in places
    ]
    # All-pairs matrix makes start -> stops, stop -> stop and stop -> start available to the planner.
    route_matrix = await routes_service.compute_matrix(nodes, nodes)
    return generate_itinerary(places, route_matrix, observations_by_place, request)


@router.post("/explain")
async def explain_itinerary(request: ItineraryExplanationRequest):
    return await ai_service.explain_itinerary(request.itinerary)
