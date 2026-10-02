"""
Developer 2 — Redemption Code Generator.

Generates cryptographically secure, unique redemption codes.
Format: TRV-XXXX-XXXX  (uppercase alphanumeric, no ambiguous chars like 0/O/1/I)
"""
from __future__ import annotations

import secrets
import string


_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"   # No 0, O, 1, I to avoid confusion


def generate_redemption_code(prefix: str = "TRV") -> str:
    """
    Generate a cryptographically secure redemption code.
    
    Format: PREFIX-XXXX-XXXX
    Example: TRV-8K4M-XP92
    
    Uses secrets.choice() which is cryptographically secure.
    """
    part1 = "".join(secrets.choice(_ALPHABET) for _ in range(4))
    part2 = "".join(secrets.choice(_ALPHABET) for _ in range(4))
    return f"{prefix}-{part1}-{part2}"
