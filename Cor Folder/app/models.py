from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, Integer, String, Text, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CrowdObservation(Base):
    __tablename__ = "crowd_observations"
    __table_args__ = (
        Index("ix_crowd_place_timestamp", "place_id", "timestamp"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    place_id: Mapped[str] = mapped_column(String(255), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
    crowd_level: Mapped[str] = mapped_column(String(30), index=True)
    source: Mapped[str] = mapped_column(String(100))
    confidence: Mapped[float] = mapped_column(Float, default=0.5)


class PlaceSeasonProfile(Base):
    __tablename__ = "place_season_profiles"
    __table_args__ = (
        UniqueConstraint("place_id", "month", name="uq_place_month"),
        Index("ix_season_place_month", "place_id", "month"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    place_id: Mapped[str] = mapped_column(String(255), index=True)
    month: Mapped[int] = mapped_column(Integer, index=True)
    weather_score: Mapped[float] = mapped_column(Float)
    crowd_score: Mapped[float] = mapped_column(Float)
    festival_score: Mapped[float] = mapped_column(Float)
    accessibility_score: Mapped[float] = mapped_column(Float)
    overall_score: Mapped[float] = mapped_column(Float)
    reason: Mapped[str] = mapped_column(Text, default="")
