from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.auth import AuthenticatedUser, require_roles
from app.database import get_db
from app.dev3_models import CommunitySubmission, ModerationAction, Review
from app.dev3_schemas import ModerationDecision
from app.api.community import _review_out, _submission_out

router = APIRouter()
MODERATOR_ROLES = ("MODERATOR", "GOVERNMENT_ADMIN", "SUPER_ADMIN")


@router.get("/queue")
def queue(user: AuthenticatedUser = Depends(require_roles(*MODERATOR_ROLES)), db: Session = Depends(get_db)):
    submissions = db.query(CommunitySubmission).filter_by(status="PENDING").order_by(CommunitySubmission.created_at.asc()).limit(100).all()
    reviews = db.query(Review).filter_by(status="PENDING").order_by(Review.created_at.asc()).limit(100).all()
    return {"submissions": [_submission_out(row) for row in submissions], "reviews": [_review_out(row) for row in reviews]}


@router.get("/history")
def history(target_type: str | None = Query(default=None, pattern="^(submission|review|user_role)$"), target_id: str | None = Query(default=None, max_length=64), user: AuthenticatedUser = Depends(require_roles(*MODERATOR_ROLES)), db: Session = Depends(get_db)):
    query = db.query(ModerationAction)
    if target_type:
        query = query.filter(ModerationAction.target_type == target_type)
    if target_id:
        query = query.filter(ModerationAction.target_id == target_id)
    actions = query.order_by(ModerationAction.created_at.desc()).limit(200).all()
    return [{"id": action.id, "moderator_id": action.moderator_id, "target_type": action.target_type, "target_id": action.target_id, "action": action.action, "note": action.note, "created_at": action.created_at} for action in actions]


@router.get("/submissions")
def list_submissions(status: str = Query(default="PENDING", pattern="^(PENDING|APPROVED|REJECTED)$"), user: AuthenticatedUser = Depends(require_roles(*MODERATOR_ROLES)), db: Session = Depends(get_db)):
    rows = db.query(CommunitySubmission).filter_by(status=status).order_by(CommunitySubmission.created_at.asc()).limit(100).all()
    return [_submission_out(row) for row in rows]


def _decide(target_type: str, target_id: str, status: str, note: str, moderator: AuthenticatedUser, db: Session):
    model = CommunitySubmission if target_type == "submission" else Review
    row = db.get(model, target_id)
    if row is None:
        raise HTTPException(status_code=404, detail={"code": "MODERATION_TARGET_NOT_FOUND", "message": "Moderation target not found"})
    if row.status != "PENDING":
        raise HTTPException(status_code=409, detail={"code": "ALREADY_MODERATED", "message": "Only pending content can be moderated"})
    row.status = status
    row.moderator_id = moderator.user_id
    row.moderator_note = note.strip()
    db.add(ModerationAction(id=secrets.token_urlsafe(18), moderator_id=moderator.user_id, target_type=target_type, target_id=target_id, action=status, note=note.strip()))
    db.commit()
    return {"id": target_id, "status": status, "moderator_id": moderator.user_id, "moderator_note": row.moderator_note}


@router.get("/submissions/{submission_id}")
def get_submission(submission_id: str, user: AuthenticatedUser = Depends(require_roles(*MODERATOR_ROLES)), db: Session = Depends(get_db)):
    row = db.get(CommunitySubmission, submission_id)
    if row is None:
        raise HTTPException(status_code=404, detail={"code": "SUBMISSION_NOT_FOUND", "message": "Submission not found"})
    return _submission_out(row)


@router.post("/submissions/{submission_id}/approve")
def approve_submission(submission_id: str, data: ModerationDecision = ModerationDecision(), user: AuthenticatedUser = Depends(require_roles(*MODERATOR_ROLES)), db: Session = Depends(get_db)):
    return _decide("submission", submission_id, "APPROVED", data.note, user, db)


@router.post("/submissions/{submission_id}/reject")
def reject_submission(submission_id: str, data: ModerationDecision = ModerationDecision(), user: AuthenticatedUser = Depends(require_roles(*MODERATOR_ROLES)), db: Session = Depends(get_db)):
    return _decide("submission", submission_id, "REJECTED", data.note, user, db)


@router.post("/reviews/{review_id}/approve")
def approve_review(review_id: str, data: ModerationDecision = ModerationDecision(), user: AuthenticatedUser = Depends(require_roles(*MODERATOR_ROLES)), db: Session = Depends(get_db)):
    return _decide("review", review_id, "APPROVED", data.note, user, db)


@router.post("/reviews/{review_id}/reject")
def reject_review(review_id: str, data: ModerationDecision = ModerationDecision(), user: AuthenticatedUser = Depends(require_roles(*MODERATOR_ROLES)), db: Session = Depends(get_db)):
    return _decide("review", review_id, "REJECTED", data.note, user, db)
