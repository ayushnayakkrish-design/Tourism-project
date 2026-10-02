"""
Developer 2 — Wallet & Points API router.

Endpoints:
  GET /api/wallet                    — get authenticated user's wallet
  GET /api/points/transactions       — paginated transaction history
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.gamification.auth_stub import CurrentUser, get_current_user
from app.gamification.schemas import PointTransactionOut, WalletOut
from app.gamification.wallet_service import WalletService

router = APIRouter()
_wallet_svc = WalletService()


@router.get("/wallet", response_model=WalletOut)
def get_wallet(
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Return the authenticated user's wallet balance."""
    wallet = _wallet_svc.get_wallet(db, current_user.user_id)
    db.commit()
    db.refresh(wallet)
    return wallet


@router.get("/points/transactions", response_model=dict)
def list_transactions(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Return paginated point transaction history for the authenticated user."""
    items, total = _wallet_svc.get_transactions(
        db, current_user.user_id, page, page_size
    )
    return {
        "items": [PointTransactionOut.model_validate(t).model_dump() for t in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
