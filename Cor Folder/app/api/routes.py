from fastapi import APIRouter

from app.schemas import Coordinates
from app.services.maps.routes_service import RoutesService

router = APIRouter()
service = RoutesService()


@router.post("/route")
async def route(origin: Coordinates, destination: Coordinates, intermediates: list[Coordinates] | None = None):
    return await service.compute_route(
        origin.model_dump(),
        destination.model_dump(),
        [x.model_dump() for x in intermediates] if intermediates else None,
    )


@router.post("/matrix")
async def matrix(origins: list[Coordinates], destinations: list[Coordinates]):
    if len(origins) > 25 or len(destinations) > 25:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail={"code": "ROUTE_MATRIX_TOO_LARGE", "message": "Each matrix dimension is limited to 25 coordinates"})
    return await service.compute_matrix(
        [x.model_dump() for x in origins],
        [x.model_dump() for x in destinations],
    )
