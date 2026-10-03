"""Developer 3 user and community database models.

The place identifier stays an opaque string owned by Developer 1's Places API.
"""
from __future__ import annotations

from datetime import datetime, timezone

from typing import Any, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(80), nullable=False)
    bio: Mapped[str] = mapped_column(Text, nullable=False, default="")
    role: Mapped[str] = mapped_column(String(32), nullable=False, default="TOURIST", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)


class UserPreference(Base):
    __tablename__ = "user_preferences"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="en")
    theme: Mapped[str] = mapped_column(String(12), nullable=False, default="system")
    voice_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    units: Mapped[str] = mapped_column(String(12), nullable=False, default="metric")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)


class CommunitySubmission(Base):
    __tablename__ = "community_submissions"
    __table_args__ = (Index("ix_community_status_created", "status", "created_at"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    photos: Mapped[list[Any]] = mapped_column(JSON, nullable=False, default=list)
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="en")
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="PENDING", index=True)
    moderator_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    moderator_note: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (
        UniqueConstraint("user_id", "place_id", name="uq_review_user_place"),
        Index("ix_reviews_place_status", "place_id", "status"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    place_id: Mapped[str] = mapped_column(String(255), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="PENDING", index=True)
    moderator_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    moderator_note: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)


class PlaceContent(Base):
    __tablename__ = "place_content"
    __table_args__ = (UniqueConstraint("place_id", "language", name="uq_place_content_language"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    place_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    language: Mapped[str] = mapped_column(String(10), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    rules: Mapped[str] = mapped_column(Text, nullable=False, default="")
    tips: Mapped[str] = mapped_column(Text, nullable=False, default="")
    source: Mapped[str] = mapped_column(String(32), nullable=False, default="community")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now)


class TranslationCache(Base):
    __tablename__ = "translation_cache"

    cache_key: Mapped[str] = mapped_column(String(64), primary_key=True)
    translation: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)


class ModerationAction(Base):
    __tablename__ = "moderation_actions"
    __table_args__ = (Index("ix_moderation_target", "target_type", "target_id"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    moderator_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    target_type: Mapped[str] = mapped_column(String(24), nullable=False)
    target_id: Mapped[str] = mapped_column(String(64), nullable=False)
    action: Mapped[str] = mapped_column(String(24), nullable=False)
    note: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utc_now)
