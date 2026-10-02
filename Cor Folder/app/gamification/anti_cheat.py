"""
Developer 2 — Anti-Cheat Service.

Performs multi-factor fraud detection on visit and proof submissions.
Returns structured decisions with reasons.
Rules are conservative: uncertain evidence → FLAGGED, not REJECTED.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Optional

from app.gamification.gps_verification import haversine_distance


# Maximum plausible human travel speed in m/s  (≈ 900 km/h — commercial flight)
MAX_PLAUSIBLE_SPEED_MPS = 250.0

# Duplicate visit window: same user, same place within this many hours = duplicate
DUPLICATE_VISIT_WINDOW_HOURS = 24

# Max visits per user per day before flagging
MAX_DAILY_VISITS = 20


@dataclass
class AntiCheatDecision:
    decision: str               # "VERIFIED" | "FLAGGED" | "REJECTED"
    reasons: list[str] = field(default_factory=list)

    def flag(self, reason: str) -> None:
        if self.decision == "VERIFIED":
            self.decision = "FLAGGED"
        if reason not in self.reasons:
            self.reasons.append(reason)

    def reject(self, reason: str) -> None:
        self.decision = "REJECTED"
        if reason not in self.reasons:
            self.reasons.append(reason)


class AntiCheatService:
    """
    Isolated anti-cheat service.

    All checks are additive — the decision starts as VERIFIED and is
    downgraded to FLAGGED or REJECTED as evidence accumulates.
    """

    # ------------------------------------------------------------------
    # Primary check: coordinates outside radius
    # ------------------------------------------------------------------

    def check_gps_distance(
        self,
        distance_metres: float,
        verification_radius: float,
        decision: AntiCheatDecision,
    ) -> None:
        if distance_metres > verification_radius:
            decision.reject("GPS_OUTSIDE_RADIUS")

    # ------------------------------------------------------------------
    # Duplicate visit check
    # ------------------------------------------------------------------

    def check_duplicate_visit(
        self,
        user_id: str,
        place_id: str,
        visit_timestamp: datetime,
        recent_visits: list,   # list of Visit ORM objects
        decision: AntiCheatDecision,
    ) -> None:
        """Flag if the same user already has a verified/flagged visit to
        the same place within the duplicate window."""
        window_start = visit_timestamp - timedelta(hours=DUPLICATE_VISIT_WINDOW_HOURS)
        for v in recent_visits:
            ts = v.timestamp
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            if ts >= window_start and v.place_id == place_id and v.status in ("VERIFIED", "FLAGGED"):
                decision.flag("DUPLICATE_VISIT")
                break

    # ------------------------------------------------------------------
    # Duplicate proof image check
    # ------------------------------------------------------------------

    def check_duplicate_proof(
        self,
        file_hash: Optional[str],
        existing_hashes: list[str],
        decision: AntiCheatDecision,
    ) -> None:
        """Reject if another visit_proof with the same SHA-256 hash exists."""
        if file_hash and file_hash in existing_hashes:
            decision.reject("DUPLICATE_PROOF_IMAGE")

    # ------------------------------------------------------------------
    # Suspicious timestamp check
    # ------------------------------------------------------------------

    def check_suspicious_timestamp(
        self,
        visit_timestamp: datetime,
        request_time: datetime,
        decision: AntiCheatDecision,
    ) -> None:
        """Flag if timestamp is more than 30 minutes in the past or any amount in the future."""
        if visit_timestamp.tzinfo is None:
            visit_timestamp = visit_timestamp.replace(tzinfo=timezone.utc)
        if request_time.tzinfo is None:
            request_time = request_time.replace(tzinfo=timezone.utc)

        diff_seconds = (request_time - visit_timestamp).total_seconds()

        if diff_seconds < 0:
            # Future timestamp (should be blocked at schema level, but double-check)
            decision.reject("FUTURE_TIMESTAMP")
        elif diff_seconds > 30 * 60:
            # Timestamp > 30 minutes ago — suspicious but not conclusive
            decision.flag("STALE_TIMESTAMP")

    # ------------------------------------------------------------------
    # Impossible travel check
    # ------------------------------------------------------------------

    def check_impossible_travel(
        self,
        user_id: str,
        visit_lat: float,
        visit_lon: float,
        visit_timestamp: datetime,
        previous_verified_visits: list,   # sorted by timestamp desc
        decision: AntiCheatDecision,
    ) -> None:
        """
        Compare this visit's location with the user's most recent verified visit.
        If the implied travel speed is physically implausible, flag.
        """
        if not previous_verified_visits:
            return

        latest = previous_verified_visits[0]
        prev_ts = latest.timestamp
        if prev_ts.tzinfo is None:
            prev_ts = prev_ts.replace(tzinfo=timezone.utc)
        if visit_timestamp.tzinfo is None:
            visit_timestamp = visit_timestamp.replace(tzinfo=timezone.utc)

        elapsed_seconds = abs((visit_timestamp - prev_ts).total_seconds())
        if elapsed_seconds < 1:
            # Same second — two visits at the same time from different locations
            dist = haversine_distance(visit_lat, visit_lon, latest.latitude, latest.longitude)
            if dist > 1000:  # More than 1km in 0 seconds
                decision.flag("IMPOSSIBLE_TRAVEL")
            return

        dist = haversine_distance(visit_lat, visit_lon, latest.latitude, latest.longitude)
        speed = dist / elapsed_seconds

        if speed > MAX_PLAUSIBLE_SPEED_MPS:
            decision.flag("IMPOSSIBLE_TRAVEL")

    # ------------------------------------------------------------------
    # Excessive reward claims
    # ------------------------------------------------------------------

    def check_excessive_claims(
        self,
        user_id: str,
        today_visit_count: int,
        decision: AntiCheatDecision,
    ) -> None:
        """Flag if a user has claimed an unusual number of visits today."""
        if today_visit_count >= MAX_DAILY_VISITS:
            decision.flag("EXCESSIVE_VISIT_CLAIMS")

    # ------------------------------------------------------------------
    # Master check — runs all sub-checks in sequence
    # ------------------------------------------------------------------

    def evaluate_visit(
        self,
        *,
        distance_metres: float,
        verification_radius: float,
        visit_lat: float,
        visit_lon: float,
        visit_timestamp: datetime,
        request_time: datetime,
        user_id: str,
        place_id: str,
        recent_visits: list,
        previous_verified_visits: list,
        today_visit_count: int,
    ) -> AntiCheatDecision:
        decision = AntiCheatDecision(decision="VERIFIED")

        self.check_gps_distance(distance_metres, verification_radius, decision)
        self.check_suspicious_timestamp(visit_timestamp, request_time, decision)
        self.check_duplicate_visit(user_id, place_id, visit_timestamp, recent_visits, decision)
        self.check_impossible_travel(
            user_id, visit_lat, visit_lon, visit_timestamp,
            previous_verified_visits, decision
        )
        self.check_excessive_claims(user_id, today_visit_count, decision)

        return decision
