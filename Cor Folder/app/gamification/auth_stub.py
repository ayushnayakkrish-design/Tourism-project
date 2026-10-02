"""
Developer 2 — Authentication stub.

Developer 3 owns the full authentication system.

This module provides:
  - CurrentUser: the minimal identity object Developer 2 needs.
  - get_current_user: FastAPI dependency that extracts the authenticated user.

DEVELOPMENT AUTH STUB:
    Since Developer 3 has not yet implemented the authentication system,
    this file provides a header-based stub for development and testing ONLY.

    The header X-User-ID is read as the user identity.
    The header X-User-Role defaults to "user" (use "admin" for admin routes).

    How to replace when Developer 3 is ready:
    1. Update CurrentUser to match Developer 3's user model.
    2. Update get_current_user to decode Developer 3's JWT/session token.
    3. Keep the same interface (user_id: str, role: str) so no other file needs changing.

IMPORTANT:
    Never trust user_id sent in the request body or query parameters.
    Always use the identity provided by get_current_user.
"""
from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException


@dataclass(frozen=True)
class CurrentUser:
    user_id: str
    role: str   # "user" | "admin"

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"


def get_current_user(
    x_user_id: str | None = Header(default=None, alias="X-User-ID"),
    x_user_role: str | None = Header(default=None, alias="X-User-Role"),
) -> CurrentUser:
    """
    DEVELOPMENT AUTH STUB — replace with Developer 3's JWT dependency.

    Reads X-User-ID and X-User-Role from request headers.
    Returns 401 if X-User-ID is missing.
    """
    if not x_user_id or not x_user_id.strip():
        raise HTTPException(
            status_code=401,
            detail={"code": "AUTHENTICATION_REQUIRED", "message": "X-User-ID header is required"},
        )
    role = (x_user_role or "user").strip().lower()
    if role not in ("user", "admin"):
        role = "user"
    return CurrentUser(user_id=x_user_id.strip(), role=role)


def require_admin(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """Dependency that requires admin role."""
    if not user.is_admin:
        raise HTTPException(
            status_code=403,
            detail={"code": "FORBIDDEN", "message": "Admin access required"},
        )
    return user
