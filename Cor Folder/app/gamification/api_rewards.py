"""
Developer 2 — Rewards & Redemption API router.

User endpoints:
  GET  /api/rewards                         — browse reward catalog
  GET  /api/rewards/{reward_id}             — get reward details
  POST /api/rewards/{reward_id}/redeem      — redeem a reward
  GET  /api/redemptions                     — user's redemption history
  GET  /api/redemptions/{redemption_id}     — specific redemption detail

Admin endpoints:
  POST   /api/admin/rewards                 — create reward
  PATCH  /api/admin/rewards/{reward_id}     — update reward
  DELETE /api/admin/rewards/{reward_id}     — deactivate reward
  GET    /api/admin/redemptions             — all redemptions (filterable)
  GET    /api/admin/reward-analytics        — aggregate stats
  POST   /api/admin/users/{user_id}/points/adjust  — manual point adjustment
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.gamification.auth_stub import CurrentUser, get_current_user, require_admin
from app.gamification.schemas import (
    PointAdjustRequest,
    RedemptionOut,
    RewardCreate,
    RewardOut,
    RewardUpdate,
)
from app.gamification.reward_service import RewardService
from app.gamification.wallet_service import WalletService

router = APIRouter()
_reward_svc = RewardService()
_wallet_svc = WalletService()


# ---------------------------------------------------------------------------
# User — Reward Catalog
# ---------------------------------------------------------------------------

@router.get("/rewards", response_model=dict, tags=["Rewards"])
def list_rewards(
    available: bool = Query(default=True),
    category: Optional[str] = Query(default=None),
    provider: Optional[str] = Query(default=None),
    minimum_points: Optional[int] = Query(default=None, ge=0),
    maximum_points: Optional[int] = Query(default=None, ge=0),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Browse the reward catalog with optional filters."""
    items, total = _reward_svc.list_rewards(
        db,
        available_only=available,
        category=category,
        provider=provider,
        min_points=minimum_points,
        max_points=maximum_points,
        page=page,
        page_size=page_size,
    )
    return {
        "items": [RewardOut.model_validate(r).model_dump() for r in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/rewards/{reward_id}", response_model=RewardOut, tags=["Rewards"])
def get_reward(
    reward_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get details for a specific reward."""
    return _reward_svc.get_reward(db, reward_id)


@router.post("/rewards/{reward_id}/redeem", status_code=201, response_model=RedemptionOut, tags=["Rewards"])
def redeem_reward(
    reward_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    Redeem a reward.  Points are deducted atomically — either everything
    succeeds or nothing changes.  Concurrent requests are protected via
    database-level row locking.
    """
    return _reward_svc.redeem(db, current_user.user_id, reward_id)


# ---------------------------------------------------------------------------
# User — Redemption History
# ---------------------------------------------------------------------------

@router.get("/redemptions", response_model=dict, tags=["Redemptions"])
def list_redemptions(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Return the authenticated user's redemption history."""
    items, total = _reward_svc.list_redemptions(
        db, current_user.user_id, page, page_size
    )
    return {
        "items": [RedemptionOut.model_validate(r).model_dump() for r in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/redemptions/{redemption_id}", response_model=RedemptionOut, tags=["Redemptions"])
def get_redemption(
    redemption_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Get a specific redemption record. Users can only see their own."""
    return _reward_svc.get_redemption(db, current_user.user_id, redemption_id)


# ---------------------------------------------------------------------------
# Admin — Reward Management
# ---------------------------------------------------------------------------

@router.post("/admin/rewards", status_code=201, response_model=RewardOut, tags=["Admin"])
def admin_create_reward(
    body: RewardCreate,
    db: Session = Depends(get_db),
    admin: CurrentUser = Depends(require_admin),
):
    """Create a new reward. Admin only."""
    data = body.model_dump()
    return _reward_svc.create_reward(db, data)


@router.patch("/admin/rewards/{reward_id}", response_model=RewardOut, tags=["Admin"])
def admin_update_reward(
    reward_id: int,
    body: RewardUpdate,
    db: Session = Depends(get_db),
    admin: CurrentUser = Depends(require_admin),
):
    """Update an existing reward. Admin only. Only provided fields are changed."""
    data = {k: v for k, v in body.model_dump().items() if v is not None}
    return _reward_svc.update_reward(db, reward_id, data)


@router.delete("/admin/rewards/{reward_id}", status_code=204, tags=["Admin"])
def admin_deactivate_reward(
    reward_id: int,
    db: Session = Depends(get_db),
    admin: CurrentUser = Depends(require_admin),
):
    """Deactivate (soft-delete) a reward. Admin only."""
    _reward_svc.delete_reward(db, reward_id)


# ---------------------------------------------------------------------------
# Admin — Redemption Management
# ---------------------------------------------------------------------------

@router.get("/admin/redemptions", response_model=dict, tags=["Admin"])
def admin_list_redemptions(
    reward_id: Optional[int] = Query(default=None),
    user_id: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    from_date: Optional[datetime] = Query(default=None),
    to_date: Optional[datetime] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    admin: CurrentUser = Depends(require_admin),
):
    """List all redemptions with optional filters. Admin only."""
    items, total = _reward_svc.admin_list_redemptions(
        db,
        reward_id=reward_id,
        user_id=user_id,
        status=status,
        from_date=from_date,
        to_date=to_date,
        page=page,
        page_size=page_size,
    )
    return {
        "items": [RedemptionOut.model_validate(r).model_dump() for r in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


# ---------------------------------------------------------------------------
# Admin — Analytics
# ---------------------------------------------------------------------------

@router.get("/admin/reward-analytics", tags=["Admin"])
def reward_analytics(
    db: Session = Depends(get_db),
    admin: CurrentUser = Depends(require_admin),
):
    """Return aggregate reward statistics. Admin only."""
    return _reward_svc.get_analytics(db)


# ---------------------------------------------------------------------------
# Admin — Point Adjustment
# ---------------------------------------------------------------------------

@router.post("/admin/users/{user_id}/points/adjust", tags=["Admin"])
def admin_adjust_points(
    user_id: str,
    body: PointAdjustRequest,
    db: Session = Depends(get_db),
    admin: CurrentUser = Depends(require_admin),
):
    """
    Manually adjust a user's point balance. Admin only.
    Every adjustment creates an ADMIN_ADJUSTMENT ledger entry.
    Cannot make balance negative.
    """
    wallet, tx = _wallet_svc.admin_adjust(
        db=db,
        user_id=user_id,
        amount=body.amount,
        reason=body.reason,
        admin_user_id=admin.user_id,
    )
    db.commit()
    db.refresh(wallet)
    return {
        "user_id": user_id,
        "new_balance": wallet.balance,
        "adjustment": body.amount,
        "transaction_id": tx.id,
        "reason": body.reason,
    }
