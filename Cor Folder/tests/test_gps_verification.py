"""
Developer 2 — Tests for GPS verification and Haversine distance.
"""
from __future__ import annotations

import math
import pytest

from app.gamification.gps_verification import haversine_distance, verify_gps


class TestHaversineDistance:
    def test_same_point_is_zero(self):
        assert haversine_distance(19.8876, 86.0945, 19.8876, 86.0945) == 0.0

    def test_known_distance_konark_to_nearby(self):
        # ~22m apart
        d = haversine_distance(19.8876, 86.0945, 19.8877, 86.0946)
        assert 10 < d < 50

    def test_known_distance_large(self):
        # Delhi to Mumbai ~1150 km
        d = haversine_distance(28.6139, 77.2090, 19.0760, 72.8777)
        assert 1_100_000 < d < 1_200_000

    def test_symmetry(self):
        d1 = haversine_distance(19.8876, 86.0945, 27.1751, 78.0421)
        d2 = haversine_distance(27.1751, 78.0421, 19.8876, 86.0945)
        assert abs(d1 - d2) < 0.01

    def test_cross_antimeridian(self):
        # Points near 180/-180 longitude
        d = haversine_distance(0.0, 179.9, 0.0, -179.9)
        assert d < 25_000  # Should be ~22km, not half the earth circumference


class TestVerifyGPS:
    def test_inside_radius(self):
        result = verify_gps(19.8878, 86.0943, 19.8876, 86.0945, 150.0)
        assert result.within_radius is True
        assert result.distance_metres < 150

    def test_outside_radius(self):
        result = verify_gps(19.9000, 86.1100, 19.8876, 86.0945, 150.0)
        assert result.within_radius is False
        assert result.distance_metres > 150

    def test_exactly_at_boundary(self):
        # Calculate exact point at 150m radius
        # 150m north of Konark
        delta_lat = 150.0 / 111_320
        result = verify_gps(
            19.8876 + delta_lat, 86.0945,
            19.8876, 86.0945,
            150.0,
        )
        # Should be right at/just outside boundary
        assert result.distance_metres >= 148

    def test_confidence_high_when_well_inside(self):
        result = verify_gps(19.8876, 86.0945, 19.8876, 86.0945, 150.0)
        assert result.confidence > 0.8

    def test_confidence_scales_near_boundary(self):
        # Just inside
        result_inside = verify_gps(19.8877, 86.0946, 19.8876, 86.0945, 150.0)
        # Well inside
        result_center = verify_gps(19.8876, 86.0945, 19.8876, 86.0945, 150.0)
        assert result_center.confidence >= result_inside.confidence

    def test_distance_stored_correctly(self):
        result = verify_gps(19.8878, 86.0943, 19.8876, 86.0945, 150.0)
        expected = haversine_distance(19.8878, 86.0943, 19.8876, 86.0945)
        assert abs(result.distance_metres - expected) < 0.01
