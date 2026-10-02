"""
Developer 2 — Wallet Service.

Manages point balances via an immutable ledger.

CRITICAL RULE:
    Every balance change MUST create a PointTransaction record.
    wallet.balance += points  is NEVER called without a ledger entry.
    Both operations must succeed atomically (single DB transaction).

    Wallet balance can NEVER go negative.
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.gamification.models import PointTransaction, TransactionType, Wallet


def _get_or_create_wallet(db: Session, user_id: str) -> Wallet:
    """Get or create the wallet for a user within the current session."""
    wallet = db.get(Wallet, user_id)
    if wallet is None:
        wallet = Wallet(user_id=user_id, balance=0)
        db.add(wallet)
        db.flush()   # Assign DB defaults; do NOT commit yet
    return wallet


class WalletService:
    """
    All wallet mutations go through this service.
    The caller must manage the transaction (begin/commit/rollback).
    """

    def get_wallet(self, db: Session, user_id: str) -> Wallet:
        """Return the user's wallet, creating it if it doesn't exist."""
        wallet = _get_or_create_wallet(db, user_id)
        db.flush()
        return wallet

    def credit(
        self,
        db: Session,
        user_id: str,
        amount: int,
        transaction_type: str,
        reference_id: str | None = None,
        description: str | None = None,
    ) -> tuple[Wallet, PointTransaction]:
        """
        Credit points to the user's wallet and create a ledger entry atomically.
        Both mutations are flushed together; caller commits.
        """
        if amount <= 0:
            raise ValueError(f"Credit amount must be positive, got {amount}")

        wallet = _get_or_create_wallet(db, user_id)
        wallet.balance += amount
        wallet.updated_at = datetime.now(timezone.utc)

        tx = PointTransaction(
            user_id=user_id,
            amount=amount,
            transaction_type=transaction_type,
            reference_id=reference_id,
            description=description,
        )
        db.add(tx)
        db.flush()
        return wallet, tx

    def debit(
        self,
        db: Session,
        user_id: str,
        amount: int,
        transaction_type: str,
        reference_id: str | None = None,
        description: str | None = None,
    ) -> tuple[Wallet, PointTransaction]:
        """
        Debit points from the user's wallet and create a ledger entry atomically.
        Raises HTTPException 422 if the wallet has insufficient funds.
        Both mutations are flushed together; caller commits.
        """
        if amount <= 0:
            raise ValueError(f"Debit amount must be positive, got {amount}")

        wallet = _get_or_create_wallet(db, user_id)

        if wallet.balance < amount:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "INSUFFICIENT_POINTS",
                    "message": f"User has {wallet.balance} points but {amount} are required",
                },
            )

        wallet.balance -= amount
        wallet.updated_at = datetime.now(timezone.utc)

        tx = PointTransaction(
            user_id=user_id,
            amount=-amount,   # Negative for debits
            transaction_type=transaction_type,
            reference_id=reference_id,
            description=description,
        )
        db.add(tx)
        db.flush()
        return wallet, tx

    def admin_adjust(
        self,
        db: Session,
        user_id: str,
        amount: int,
        reason: str,
        admin_user_id: str,
    ) -> tuple[Wallet, PointTransaction]:
        """
        Admin point adjustment. Amount can be positive or negative.
        Cannot make balance negative.
        Always creates an ADMIN_ADJUSTMENT ledger entry.
        """
        wallet = _get_or_create_wallet(db, user_id)

        new_balance = wallet.balance + amount
        if new_balance < 0:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "INSUFFICIENT_POINTS",
                    "message": f"Adjustment would make balance negative (current: {wallet.balance}, adjustment: {amount})",
                },
            )

        wallet.balance = new_balance
        wallet.updated_at = datetime.now(timezone.utc)

        tx = PointTransaction(
            user_id=user_id,
            amount=amount,
            transaction_type=TransactionType.ADMIN_ADJUSTMENT,
            reference_id=None,
            description=f"Admin adjustment by {admin_user_id}: {reason}",
        )
        db.add(tx)
        db.flush()
        return wallet, tx

    def get_transactions(
        self,
        db: Session,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[PointTransaction], int]:
        """Return paginated transaction history for a user."""
        base_q = db.query(PointTransaction).filter(PointTransaction.user_id == user_id)
        total = base_q.count()
        items = (
            base_q
            .order_by(PointTransaction.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return items, total
