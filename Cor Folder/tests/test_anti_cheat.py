"""
Developer 2 — Tests for Anti-Cheat Service.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from app.gamification.anti_cheat import AntiCheatDecision, AntiCheatService


def _visit(place_id, status, lat, lon, ts):
    return SimpleNamespace(
        place_id=place_id,
        status=status,
        latitude=lat,
        longitude=lon,
        timestamp=ts,
    )


NOW = datetime(2026, 10, 2, 17, 30, 0, tzinfo=timezone.utc)
PLACE_LAT, PLACE_LON = 19.8876, 86.0945


class TestGPSDistanceCheck:
    def test_outside_radius_rejects(self):
        svc = AntiCheatService()
        d = AntiCheatDecision(decision="VERIFIED")
        svc.check_gps_distance(200.0, 150.0, d)
        assert d.decision == "REJECTED"
        assert "GPS_OUTSIDE_RADIUS" in d.reasons

    def test_inside_radius_no_change(self):
        svc = AntiCheatService()
        d = AntiCheatDecision(decision="VERIFIED")
        svc.check_gps_distance(100.0, 150.0, d)
        assert d.decision == "VERIFIED"
        assert not d.reasons

    def test_exactly_at_boundary_passes(self):
        svc = AntiCheatService()
        d = AntiCheatDecision(decision="VERIFIED")
        svc.check_gps_distance(150.0, 150.0, d)
        assert d.decision == "VERIFIED"


class TestDuplicateVisitCheck:
    def test_same_place_within_window_flags(self):
        svc = AntiCheatService()
        d = AntiCheatDecision(decision="VERIFIED")
        recent = [
            _visit("PLACE-1", "VERIFIED", PLACE_LAT, PLACE_LON, NOW - timedelta(hours=1))
        ]
        svc.check_duplicate_visit("user1", "PLACE-1", NOW, recent, d)
        assert d.decision == "FLAGGED"
        assert "DUPLICATE_VISIT" in d.reasons

    def test_different_place_no_flag(self):
        svc = AntiCheatService()
        d = AntiCheatDecision(decision="VERIFIED")
        recent = [
            _visit("PLACE-2", "VERIFIED", PLACE_LAT, PLACE_LON, NOW - timedelta(hours=1))
        ]
        svc.check_duplicate_visit("user1", "PLACE-1", NOW, recent, d)
        assert d.decision == "VERIFIED"

    def test_outside_window_no_flag(self):
        svc = AntiCheatService()
        d = AntiCheatDecision(decision="VERIFIED")
        recent = [
            _visit("PLACE-1", "VERIFIED", PLACE_LAT, PLACE_LON, NOW - timedelta(hours=25))
        ]
        svc.check_duplicate_visit("user1", "PLACE-1", NOW, recent, d)
        assert d.decision == "VERIFIED"

    def test_rejected_status_not_counted(self):
        svc = AntiCheatService()
        d = AntiCheatDecision(decision="VERIFIED")
        recent = [
            _visit("PLACE-1", "REJECTED", PLACE_LAT, PLACE_LON, NOW - timedelta(hours=1))
        ]
        svc.check_duplicate_visit("user1", "PLACE-1", NOW, recent, d)
        assert d.decision == "VERIFIED"


class TestDuplicateProofCheck:
    def test_duplicate_hash_rejects(self):
        svc = AntiCheatService()
        d = AntiCheatDecision(decision="VERIFIED")
        svc.check_duplicate_proof("abc123", ["abc123", "def456"], d)
        assert d.decision == "REJECTED"
        assert "DUPLICATE_PROOF_IMAGE" in d.reasons

    def test_unique_hash_no_change(self):
        svc = AntiCheatService()
        d = AntiCheatDecision(decision="VERIFIED")
        svc.check_duplicate_proof("newHash", ["abc123", "def456"], d)
        assert d.decision == "VERIFIED"

    def test_none_hash_no_change(self):
        svc = AntiCheatService()
        d = AntiCheatDecision(decision="VERIFIED")
        svc.check_duplicate_proof(None, ["abc123"], d)
        assert d.decision == "VERIFIED"


class TestSuspiciousTimestampCheck:
    def test_future_timestamp_rejects(self):
        svc = AntiCheatService()
        d = AntiCheatDecision(decision="VERIFIED")
        svc.check_suspicious_timestamp(NOW + timedelta(minutes=5), NOW, d)
        assert d.decision == "REJECTED"
        assert "FUTURE_TIMESTAMP" in d.reasons

    def test_stale_timestamp_flags(self):
        svc = AntiCheatService()
        d = AntiCheatDecision(decision="VERIFIED")
        svc.check_suspicious_timestamp(NOW - timedelta(hours=2), NOW, d)
        assert d.decision == "FLAGGED"
        assert "STALE_TIMESTAMP" in d.reasons

    def test_recent_timestamp_ok(self):
        svc = AntiCheatService()
        d = AntiCheatDecision(decision="VERIFIED")
        svc.check_suspicious_timestamp(NOW - timedelta(minutes=5), NOW, d)
        assert d.decision == "VERIFIED"


class TestImpossibleTravelCheck:
    def test_impossible_speed_flags(self):
        svc = AntiCheatService()
        d = AntiCheatDecision(decision="VERIFIED")
        # Delhi to Mumbai (~1150km) in 10 seconds — impossible
        prev = [_visit("PLACE-DELHI", "VERIFIED", 28.6139, 77.2090, NOW - timedelta(seconds=10))]
        svc.check_impossible_travel("user1", 19.0760, 72.8777, NOW, prev, d)
        assert d.decision == "FLAGGED"
        assert "IMPOSSIBLE_TRAVEL" in d.reasons

    def test_plausible_travel_no_flag(self):
        svc = AntiCheatService()
        d = AntiCheatDecision(decision="VERIFIED")
        # 200m in 5 minutes — walking speed
        prev = [_visit("PLACE-1", "VERIFIED", 19.8874, 86.0943, NOW - timedelta(minutes=5))]
        svc.check_impossible_travel("user1", 19.8876, 86.0945, NOW, prev, d)
        assert d.decision == "VERIFIED"

    def test_no_previous_visits_no_flag(self):
        svc = AntiCheatService()
        d = AntiCheatDecision(decision="VERIFIED")
        svc.check_impossible_travel("user1", 19.8876, 86.0945, NOW, [], d)
        assert d.decision == "VERIFIED"


class TestExcessiveClaims:
    def test_over_limit_flags(self):
        svc = AntiCheatService()
        d = AntiCheatDecision(decision="VERIFIED")
        svc.check_excessive_claims("user1", 25, d)
        assert d.decision == "FLAGGED"
        assert "EXCESSIVE_VISIT_CLAIMS" in d.reasons

    def test_under_limit_no_flag(self):
        svc = AntiCheatService()
        d = AntiCheatDecision(decision="VERIFIED")
        svc.check_excessive_claims("user1", 5, d)
        assert d.decision == "VERIFIED"


class TestEvaluateVisit:
    def test_clean_visit_verified(self):
        svc = AntiCheatService()
        result = svc.evaluate_visit(
            distance_metres=50.0,
            verification_radius=150.0,
            visit_lat=PLACE_LAT,
            visit_lon=PLACE_LON,
            visit_timestamp=NOW,
            request_time=NOW,
            user_id="user1",
            place_id="PLACE-1",
            recent_visits=[],
            previous_verified_visits=[],
            today_visit_count=1,
        )
        assert result.decision == "VERIFIED"
        assert not result.reasons

    def test_outside_radius_rejects(self):
        svc = AntiCheatService()
        result = svc.evaluate_visit(
            distance_metres=500.0,
            verification_radius=150.0,
            visit_lat=PLACE_LAT + 0.01,
            visit_lon=PLACE_LON,
            visit_timestamp=NOW,
            request_time=NOW,
            user_id="user1",
            place_id="PLACE-1",
            recent_visits=[],
            previous_verified_visits=[],
            today_visit_count=1,
        )
        assert result.decision == "REJECTED"

    def test_multiple_flags_accumulate(self):
        svc = AntiCheatService()
        recent = [
            _visit("PLACE-1", "VERIFIED", PLACE_LAT, PLACE_LON, NOW - timedelta(hours=1))
        ]
        result = svc.evaluate_visit(
            distance_metres=50.0,
            verification_radius=150.0,
            visit_lat=PLACE_LAT,
            visit_lon=PLACE_LON,
            visit_timestamp=NOW - timedelta(hours=2),  # stale
            request_time=NOW,
            user_id="user1",
            place_id="PLACE-1",
            recent_visits=recent,
            previous_verified_visits=[],
            today_visit_count=1,
        )
        assert result.decision == "FLAGGED"
        assert len(result.reasons) >= 2
