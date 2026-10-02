"""
Developer 2 — Gamification database models.

Uses Optional[X] from typing (not X | None) for Python 3.14 compat with SQLAlchemy 2.1.
Composite indexes are declared per-column (index=True) to avoid global metadata
double-registration issues in test fixtures.
"""
from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class VisitStatus(str, enum.Enum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    FLAGGED = "FLAGGED"


class VerificationMethod(str, enum.Enum):
    GPS = "GPS"
    GPS_PHOTO = "GPS_PHOTO"
    MANUAL = "MANUAL"


class ProofStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class TransactionType(str, enum.Enum):
    VISIT_REWARD = "VISIT_REWARD"
    PHOTO_REWARD = "PHOTO_REWARD"
    BONUS = "BONUS"
    REDEMPTION = "REDEMPTION"
    ADMIN_ADJUSTMENT = "ADMIN_ADJUSTMENT"
    REVERSAL = "REVERSAL"


class RewardStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    EXPIRED = "EXPIRED"
    OUT_OF_STOCK = "OUT_OF_STOCK"


class RedemptionStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    USED = "USED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


# ---------------------------------------------------------------------------
# Visit
# ---------------------------------------------------------------------------

class Visit(Base):
    __tablename__ = "visits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    place_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    status: Mapped[str] = mapped_column(String(20), nullable=False, default=VisitStatus.PENDING, index=True)
    verification_method: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    verification_radius: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    distance_from_place: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    visit_reward_granted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    photo_reward_granted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utc_now, onupdate=_utc_now)

    proofs: Mapped[list[VisitProof]] = relationship(
        "VisitProof", back_populates="visit", cascade="all, delete-orphan"
    )


# ---------------------------------------------------------------------------
# Visit Proof
# ---------------------------------------------------------------------------

class VisitProof(Base):
    __tablename__ = "visit_proofs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    visit_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("visits.id", ondelete="CASCADE"), nullable=False, index=True
    )
    image_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    verification_status: Mapped[str] = mapped_column(String(20), nullable=False, default=ProofStatus.PENDING)
    file_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utc_now)

    visit: Mapped[Visit] = relationship("Visit", back_populates="proofs")


# ---------------------------------------------------------------------------
# Wallet
# ---------------------------------------------------------------------------

class Wallet(Base):
    __tablename__ = "wallets"
    __table_args__ = (UniqueConstraint("user_id", name="uq_wallets_user_id"),)

    user_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    balance: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utc_now, onupdate=_utc_now)


# ---------------------------------------------------------------------------
# Point Transaction
# ---------------------------------------------------------------------------

class PointTransaction(Base):
    __tablename__ = "point_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    reference_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utc_now, index=True)


# ---------------------------------------------------------------------------
# Reward
# ---------------------------------------------------------------------------

class Reward(Base):
    __tablename__ = "rewards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    provider: Mapped[str] = mapped_column(String(255), nullable=False, default="", index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False, default="general", index=True)
    points_required: Mapped[int] = mapped_column(Integer, nullable=False)
    stock: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    valid_from: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    valid_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=RewardStatus.ACTIVE, index=True)
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utc_now, onupdate=_utc_now)


# ---------------------------------------------------------------------------
# Redemption
# ---------------------------------------------------------------------------

class Redemption(Base):
    __tablename__ = "redemptions"
    __table_args__ = (UniqueConstraint("redemption_code", name="uq_redemption_code"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    reward_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("rewards.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    points_spent: Mapped[int] = mapped_column(Integer, nullable=False)
    redemption_code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=RedemptionStatus.ACTIVE, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_utc_now)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    redeemed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    reward: Mapped[Reward] = relationship("Reward", lazy="select")
