"""
Developer 2 — Reward Service.

Manages the reward catalog and redemption process.
Redemption is fully atomic — any failure triggers rollback.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.gamification.code_service import generate_redemption_code
from app.gamification.models import (
    PointTransaction,
    Redemption,
    RedemptionStatus,
    Reward,
    RewardStatus,
    TransactionType,
)
from app.gamification.wallet_service import WalletService

_wallet_svc = WalletService()


class RewardService:

    # ------------------------------------------------------------------
    # Catalog queries
    # ------------------------------------------------------------------

    def list_rewards(
        self,
        db: Session,
        available_only: bool = True,
        category: Optional[str] = None,
        provider: Optional[str] = None,
        min_points: Optional[int] = None,
        max_points: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Reward], int]:
        now = datetime.now(timezone.utc)
        q = db.query(Reward)

        if available_only:
            q = q.filter(Reward.status == RewardStatus.ACTIVE)
            q = q.filter(
                (Reward.valid_from == None) | (Reward.valid_from <= now)
            )
            q = q.filter(
                (Reward.valid_until == None) | (Reward.valid_until > now)
            )
            q = q.filter(
                (Reward.stock == None) | (Reward.stock > 0)
            )

        if category:
            q = q.filter(Reward.category == category)
        if provider:
            q = q.filter(Reward.provider == provider)
        if min_points is not None:
            q = q.filter(Reward.points_required >= min_points)
        if max_points is not None:
            q = q.filter(Reward.points_required <= max_points)

        total = q.count()
        items = (
            q.order_by(Reward.points_required.asc(), Reward.id.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return items, total

    def get_reward(self, db: Session, reward_id: int) -> Reward:
        reward = db.get(Reward, reward_id)
        if reward is None:
            raise HTTPException(
                status_code=404,
                detail={"code": "REWARD_NOT_FOUND", "message": "Reward not found"},
            )
        return reward

    # ------------------------------------------------------------------
    # Admin CRUD
    # ------------------------------------------------------------------

    def create_reward(self, db: Session, data: dict) -> Reward:
        metadata = data.pop("metadata", None)
        reward = Reward(**data, metadata_=metadata)
        db.add(reward)
        db.commit()
        db.refresh(reward)
        return reward

    def update_reward(self, db: Session, reward_id: int, data: dict) -> Reward:
        reward = self.get_reward(db, reward_id)
        for key, value in data.items():
            if key == "metadata":
                reward.metadata_ = value
            elif hasattr(reward, key):
                setattr(reward, key, value)
        reward.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(reward)
        return reward

    def delete_reward(self, db: Session, reward_id: int) -> None:
        reward = self.get_reward(db, reward_id)
        reward.status = RewardStatus.INACTIVE
        reward.updated_at = datetime.now(timezone.utc)
        db.commit()

    # ------------------------------------------------------------------
    # Redemption
    # ------------------------------------------------------------------

    def redeem(self, db: Session, user_id: str, reward_id: int) -> Redemption:
        """
        Atomic redemption flow:
        1. Load and lock reward (SELECT FOR UPDATE)
        2. Check reward availability
        3. Debit wallet
        4. Decrement stock
        5. Generate unique redemption code
        6. Create redemption record
        7. Commit — all or nothing

        Uses SELECT FOR UPDATE to prevent concurrent over-redemptions.
        """
        now = datetime.now(timezone.utc)

        # Step 1: Lock the reward row to prevent race conditions
        reward = (
            db.query(Reward)
            .filter(Reward.id == reward_id)
            .with_for_update()
            .first()
        )
        if reward is None:
            raise HTTPException(
                status_code=404,
                detail={"code": "REWARD_NOT_FOUND", "message": "Reward not found"},
            )

        # Step 2: Availability checks
        if reward.status != RewardStatus.ACTIVE:
            raise HTTPException(
                status_code=422,
                detail={"code": "REWARD_UNAVAILABLE", "message": "Reward is not active"},
            )
        if reward.valid_from and now < reward.valid_from:
            raise HTTPException(
                status_code=422,
                detail={"code": "REWARD_UNAVAILABLE", "message": "Reward is not yet available"},
            )
        if reward.valid_until and now >= reward.valid_until:
            raise HTTPException(
                status_code=422,
                detail={"code": "REWARD_EXPIRED", "message": "Reward has expired"},
            )
        if reward.stock is not None and reward.stock <= 0:
            raise HTTPException(
                status_code=422,
                detail={"code": "OUT_OF_STOCK", "message": "Reward is out of stock"},
            )

        # Step 3: Debit wallet (raises INSUFFICIENT_POINTS if not enough)
        # This also locks the wallet row implicitly through get_or_create + flush
        _wallet_svc.debit(
            db=db,
            user_id=user_id,
            amount=reward.points_required,
            transaction_type=TransactionType.REDEMPTION,
            reference_id=None,  # Will be updated after redemption is created
            description=f"Redeemed: {reward.name}",
        )

        # Step 4: Decrement stock
        if reward.stock is not None:
            reward.stock -= 1
            if reward.stock == 0:
                reward.status = RewardStatus.OUT_OF_STOCK
            reward.updated_at = now
        db.flush()

        # Step 5: Generate unique redemption code (retry on collision)
        for _attempt in range(10):
            code = generate_redemption_code()
            existing = db.query(Redemption).filter(Redemption.redemption_code == code).first()
            if existing is None:
                break
        else:
            raise HTTPException(
                status_code=500,
                detail={"code": "REDEMPTION_FAILED", "message": "Could not generate unique redemption code"},
            )

        # Step 6: Create redemption record
        redemption = Redemption(
            user_id=user_id,
            reward_id=reward.id,
            points_spent=reward.points_required,
            redemption_code=code,
            status=RedemptionStatus.ACTIVE,
            expires_at=reward.valid_until,
        )
        db.add(redemption)
        db.flush()

        # Update the transaction reference_id to point to the redemption
        tx = (
            db.query(PointTransaction)
            .filter(
                PointTransaction.user_id == user_id,
                PointTransaction.transaction_type == TransactionType.REDEMPTION,
                PointTransaction.reference_id == None,
            )
            .order_by(PointTransaction.created_at.desc())
            .first()
        )
        if tx:
            tx.reference_id = str(redemption.id)
            db.flush()

        # Step 7: Commit
        db.commit()
        db.refresh(redemption)
        return redemption

    # ------------------------------------------------------------------
    # Redemption history
    # ------------------------------------------------------------------

    def list_redemptions(
        self,
        db: Session,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Redemption], int]:
        q = db.query(Redemption).filter(Redemption.user_id == user_id)
        total = q.count()
        items = (
            q.order_by(Redemption.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return items, total

    def get_redemption(self, db: Session, user_id: str, redemption_id: int) -> Redemption:
        r = db.get(Redemption, redemption_id)
        if r is None:
            raise HTTPException(
                status_code=404,
                detail={"code": "REDEMPTION_NOT_FOUND", "message": "Redemption not found"},
            )
        if r.user_id != user_id:
            raise HTTPException(
                status_code=403,
                detail={"code": "FORBIDDEN", "message": "You do not own this redemption"},
            )
        return r

    # ------------------------------------------------------------------
    # Admin — list all redemptions
    # ------------------------------------------------------------------

    def admin_list_redemptions(
        self,
        db: Session,
        reward_id: Optional[int] = None,
        user_id: Optional[str] = None,
        status: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Redemption], int]:
        q = db.query(Redemption)
        if reward_id is not None:
            q = q.filter(Redemption.reward_id == reward_id)
        if user_id:
            q = q.filter(Redemption.user_id == user_id)
        if status:
            q = q.filter(Redemption.status == status)
        if from_date:
            q = q.filter(Redemption.created_at >= from_date)
        if to_date:
            q = q.filter(Redemption.created_at <= to_date)
        total = q.count()
        items = (
            q.order_by(Redemption.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return items, total

    # ------------------------------------------------------------------
    # Analytics
    # ------------------------------------------------------------------

    def get_analytics(self, db: Session) -> dict:
        total_redemptions = db.query(func.count(Redemption.id)).scalar() or 0
        total_points = (
            db.query(func.sum(Redemption.points_spent)).scalar() or 0
        )
        active_rewards = (
            db.query(func.count(Reward.id))
            .filter(Reward.status == RewardStatus.ACTIVE)
            .scalar() or 0
        )

        # Per-reward stats
        per_reward_rows = (
            db.query(
                Reward.id,
                Reward.name,
                Reward.points_required,
                Reward.stock,
                Reward.status,
                func.count(Redemption.id).label("redemption_count"),
                func.sum(Redemption.points_spent).label("points_redeemed"),
            )
            .outerjoin(Redemption, Redemption.reward_id == Reward.id)
            .group_by(Reward.id)
            .all()
        )
        per_reward = [
            {
                "reward_id": r.id,
                "name": r.name,
                "points_required": r.points_required,
                "stock": r.stock,
                "status": r.status,
                "redemption_count": r.redemption_count or 0,
                "points_redeemed": r.points_redeemed or 0,
            }
            for r in per_reward_rows
        ]

        # Per-provider stats
        per_provider_rows = (
            db.query(
                Reward.provider,
                func.count(Redemption.id).label("redemption_count"),
                func.sum(Redemption.points_spent).label("points_redeemed"),
            )
            .outerjoin(Redemption, Redemption.reward_id == Reward.id)
            .group_by(Reward.provider)
            .all()
        )
        per_provider = [
            {
                "provider": r.provider,
                "redemption_count": r.redemption_count or 0,
                "points_redeemed": r.points_redeemed or 0,
            }
            for r in per_provider_rows
        ]

        return {
            "total_redemptions": total_redemptions,
            "total_points_redeemed": int(total_points),
            "active_rewards": active_rewards,
            "per_reward": per_reward,
            "per_provider": per_provider,
        }
