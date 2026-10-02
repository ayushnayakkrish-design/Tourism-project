"""
Developer 2 — GPS Verification Service.

Implements Haversine distance calculation and visit verification logic.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on earth (in metres).
    Uses the Haversine formula.
    """
    R = 6_371_000.0  # Earth radius in metres

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


@dataclass(frozen=True)
class GPSVerificationResult:
    distance_metres: float
    verification_radius: float
    within_radius: bool
    confidence: float       # 0.0–1.0; lower when very close to boundary


def verify_gps(
    user_lat: float,
    user_lon: float,
    place_lat: float,
    place_lon: float,
    verification_radius: float,
) -> GPSVerificationResult:
    """
    Determine whether the user's GPS coordinates are within the allowed radius
    of the destination.

    Returns a GPSVerificationResult with distance and a within_radius flag.
    A confidence score reflects how convincingly the user is inside or outside.
    """
    dist = haversine_distance(user_lat, user_lon, place_lat, place_lon)
    within = dist <= verification_radius

    # Confidence: 1.0 when well inside, degrades near boundary, never below 0.1
    if within:
        # Fraction of radius consumed — small fraction = high confidence
        ratio = dist / verification_radius if verification_radius > 0 else 0.0
        confidence = max(0.1, 1.0 - ratio * 0.5)
    else:
        # How far outside relative to radius
        overshoot = (dist - verification_radius) / verification_radius if verification_radius > 0 else 1.0
        confidence = max(0.1, min(0.9, overshoot))

    return GPSVerificationResult(
        distance_metres=round(dist, 2),
        verification_radius=verification_radius,
        within_radius=within,
        confidence=round(confidence, 3),
    )
