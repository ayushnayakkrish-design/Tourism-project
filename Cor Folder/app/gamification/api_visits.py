"""
Developer 2 — Visit API router.

Endpoints:
  POST /api/visits              — create and verify a visit
  GET  /api/visits              — list authenticated user's visits
  GET  /api/visits/{visit_id}   — get a specific visit
  POST /api/visits/{visit_id}/proof — upload photo proof
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.gamification.auth_stub import CurrentUser, get_current_user
from app.gamification.place_provider import get_place_provider
from app.gamification.schemas import VisitCreate, VisitOut, VisitProofOut
from app.gamification.storage_provider import get_storage_provider
from app.gamification.visit_service import VisitService

router = APIRouter()


def _visit_service() -> VisitService:
    return VisitService(get_place_provider(), get_storage_provider())


@router.post("", status_code=201, response_model=VisitOut)
async def create_visit(
    body: VisitCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Submit a new visit with GPS coordinates for verification.
    The authenticated user identity comes from the auth system — never the request body.
    """
    svc = _visit_service()
    visit = await svc.create_visit(
        db=db,
        user_id=current_user.user_id,
        place_id=body.place_id,
        user_lat=body.latitude,
        user_lon=body.longitude,
        visit_timestamp=body.timestamp,
    )
    return visit


@router.get("", response_model=dict)
def list_visits(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """List the authenticated user's visits with pagination."""
    svc = _visit_service()
    items, total = svc.list_visits(db, current_user.user_id, page, page_size)
    return {
        "items": [VisitOut.model_validate(v).model_dump() for v in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{visit_id}", response_model=VisitOut)
def get_visit(
    visit_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get a specific visit. Users can only access their own visits."""
    svc = _visit_service()
    return svc.get_visit(db, current_user.user_id, visit_id)


@router.post("/{visit_id}/proof", status_code=201, response_model=VisitProofOut)
async def upload_proof(
    visit_id: int,
    file: UploadFile = File(...),
    latitude: Optional[float] = Form(default=None),
    longitude: Optional[float] = Form(default=None),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Upload a photo as proof for a visit.
    Multipart form upload. Optional latitude/longitude from photo metadata.
    """
    svc = _visit_service()
    proof = await svc.upload_proof(
        db=db,
        user_id=current_user.user_id,
        visit_id=visit_id,
        file=file,
        proof_lat=latitude,
        proof_lon=longitude,
    )
    return proof
