from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.auth import AuthenticatedUser, get_authenticated_user
from app.database import get_db
from app.dev3_models import CommunitySubmission, Review
from app.dev3_schemas import ReviewCreate, SubmissionCreate

router = APIRouter()


def _submission_out(row: CommunitySubmission) -> dict:
    return {"id": row.id, "user_id": row.user_id, "type": row.type, "name": row.name, "latitude": row.latitude, "longitude": row.longitude, "description": row.description, "photos": row.photos, "language": row.language, "status": row.status, "moderator_note": row.moderator_note, "created_at": row.created_at}


def _review_out(row: Review) -> dict:
    return {"id": row.id, "user_id": row.user_id, "place_id": row.place_id, "rating": row.rating, "comment": row.comment, "status": row.status, "created_at": row.created_at}


@router.post("/community/places", status_code=201)
def create_submission(data: SubmissionCreate, user: AuthenticatedUser = Depends(get_authenticated_user), db: Session = Depends(get_db)):
    row = CommunitySubmission(id=secrets.token_urlsafe(18), user_id=user.user_id, **data.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return _submission_out(row)


@router.get("/community/places/mine")
@router.get("/users/me/submissions", include_in_schema=False)
def my_submissions(user: AuthenticatedUser = Depends(get_authenticated_user), db: Session = Depends(get_db)):
    rows = db.query(CommunitySubmission).filter(CommunitySubmission.user_id == user.user_id).order_by(CommunitySubmission.created_at.desc()).all()
    return [_submission_out(row) for row in rows]


@router.get("/community/places")
def approved_submissions(type: str | None = Query(default=None, max_length=40), db: Session = Depends(get_db)):
    query = db.query(CommunitySubmission).filter(CommunitySubmission.status == "APPROVED")
    if type:
        query = query.filter(CommunitySubmission.type == type)
    return [_submission_out(row) for row in query.order_by(CommunitySubmission.created_at.desc()).limit(100).all()]


@router.get("/community/places/{submission_id}")
def get_approved_submission(submission_id: str, db: Session = Depends(get_db)):
    row = db.query(CommunitySubmission).filter_by(id=submission_id, status="APPROVED").first()
    if row is None:
        raise HTTPException(status_code=404, detail={"code": "SUBMISSION_NOT_FOUND", "message": "Approved submission not found"})
    return _submission_out(row)


@router.post("/community/reviews", status_code=201)
def create_review(data: ReviewCreate, user: AuthenticatedUser = Depends(get_authenticated_user), db: Session = Depends(get_db)):
    row = Review(id=secrets.token_urlsafe(18), user_id=user.user_id, place_id=data.place_id.strip(), rating=data.rating, comment=data.comment.strip())
    db.add(row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail={"code": "REVIEW_EXISTS", "message": "You have already reviewed this place"})
    db.refresh(row)
    return _review_out(row)


@router.get("/places/{place_id}/reviews")
def list_reviews(place_id: str, db: Session = Depends(get_db)):
    rows = db.query(Review).filter_by(place_id=place_id, status="APPROVED").order_by(Review.created_at.desc()).limit(100).all()
    return [_review_out(row) for row in rows]
