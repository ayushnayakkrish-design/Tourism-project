"""
Developer 2 authentication adapter.

Developer 3 supplies the bearer-token identity. This module preserves the
CurrentUser(user_id, role) interface used throughout Developer 2's routers.
Client-supplied X-User-ID and X-User-Role headers are not authentication.
"""
from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, HTTPException

from app.core.auth import AuthenticatedUser, get_authenticated_user


@dataclass(frozen=True)
class CurrentUser:
    user_id: str
    role: str   # "user" | "admin"

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"


def get_current_user(user: AuthenticatedUser = Depends(get_authenticated_user)) -> CurrentUser:
    """Adapt Developer 3 bearer identity to Developer 2's stable interface."""
    role = "admin" if user.role == "SUPER_ADMIN" else "user"
    return CurrentUser(user_id=user.user_id, role=role)


def require_admin(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    """Dependency that requires admin role."""
    if not user.is_admin:
        raise HTTPException(
            status_code=403,
            detail={"code": "FORBIDDEN", "message": "Admin access required"},
        )
    return user
