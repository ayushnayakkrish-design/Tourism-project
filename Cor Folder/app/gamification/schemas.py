"""
Developer 2 — Pydantic schemas for the Gamification system.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ---------------------------------------------------------------------------
# Visit
# ---------------------------------------------------------------------------

class VisitCreate(BaseModel):
    place_id: str = Field(min_length=1, max_length=255)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    timestamp: datetime

    @field_validator("timestamp")
    @classmethod
    def timestamp_not_future(cls, v: datetime) -> datetime:
        from datetime import timezone
        now = datetime.now(timezone.utc)
        if v.tzinfo is None:
            from datetime import timezone as tz
            v = v.replace(tzinfo=tz.utc)
        if v > now:
            raise ValueError("timestamp cannot be in the future")
        return v


class VisitOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: str
    place_id: str
    latitude: float
    longitude: float
    timestamp: datetime
    status: str
    verification_method: Optional[str]
    verification_radius: Optional[float]
    distance_from_place: Optional[float]
    rejection_reason: Optional[str]
    visit_reward_granted: bool
    photo_reward_granted: bool
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Visit Proof
# ---------------------------------------------------------------------------

class VisitProofOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    visit_id: int
    image_url: str
    latitude: Optional[float]
    longitude: Optional[float]
    timestamp: Optional[datetime]
    verification_status: str
    file_hash: Optional[str]
    created_at: datetime


# ---------------------------------------------------------------------------
# Wallet
# ---------------------------------------------------------------------------

class WalletOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    balance: int
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Point Transaction
# ---------------------------------------------------------------------------

class PointTransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: str
    amount: int
    transaction_type: str
    reference_id: Optional[str]
    description: Optional[str]
    created_at: datetime


class PointTransactionPage(BaseModel):
    items: list[PointTransactionOut]
    total: int
    page: int
    page_size: int


# ---------------------------------------------------------------------------
# Reward
# ---------------------------------------------------------------------------

class RewardCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str = Field(default="", max_length=4000)
    provider: str = Field(default="", max_length=255)
    category: str = Field(default="general", max_length=100)
    points_required: int = Field(ge=1)
    stock: Optional[int] = Field(default=None, ge=0)
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    metadata: Optional[dict[str, Any]] = None


class RewardUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=4000)
    provider: Optional[str] = Field(default=None, max_length=255)
    category: Optional[str] = Field(default=None, max_length=100)
    points_required: Optional[int] = Field(default=None, ge=1)
    stock: Optional[int] = Field(default=None, ge=0)
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    status: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class RewardOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    provider: str
    category: str
    points_required: int
    stock: Optional[int]
    valid_from: Optional[datetime]
    valid_until: Optional[datetime]
    status: str
    created_at: datetime
    updated_at: datetime


class RewardPage(BaseModel):
    items: list[RewardOut]
    total: int
    page: int
    page_size: int


# ---------------------------------------------------------------------------
# Redemption
# ---------------------------------------------------------------------------

class RedemptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: str
    reward_id: int
    points_spent: int
    redemption_code: str
    status: str
    created_at: datetime
    expires_at: Optional[datetime]
    redeemed_at: Optional[datetime]


class RedemptionPage(BaseModel):
    items: list[RedemptionOut]
    total: int
    page: int
    page_size: int


# ---------------------------------------------------------------------------
# Admin — Point Adjustment
# ---------------------------------------------------------------------------

class PointAdjustRequest(BaseModel):
    amount: int = Field(description="Positive to credit, negative to debit. Cannot make balance negative.")
    reason: str = Field(min_length=1, max_length=500)


# ---------------------------------------------------------------------------
# Reward Analytics
# ---------------------------------------------------------------------------

class RewardAnalyticsOut(BaseModel):
    total_redemptions: int
    total_points_redeemed: int
    active_rewards: int
    per_reward: list[dict]
    per_provider: list[dict]
