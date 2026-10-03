from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from dataclasses import dataclass

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dev3_models import User

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthenticatedUser:
    user_id: str
    email: str
    display_name: str
    role: str


def _b64e(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64d(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def create_access_token(user: User, now: int | None = None) -> str:
    issued_at = int(time.time()) if now is None else now
    header = _b64e(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
    payload = _b64e(json.dumps({"sub": user.id, "iat": issued_at, "exp": issued_at + settings.ACCESS_TOKEN_MINUTES * 60}, separators=(",", ":")).encode())
    signing_input = f"{header}.{payload}"
    signature = _b64e(hmac.new(settings.AUTH_SECRET.encode(), signing_input.encode(), hashlib.sha256).digest())
    return f"{signing_input}.{signature}"


def _subject_from_token(token: str, now: int | None = None) -> str:
    try:
        header, payload, signature = token.split(".")
        parsed_header = json.loads(_b64d(header))
        claims = json.loads(_b64d(payload))
        if parsed_header != {"alg": "HS256", "typ": "JWT"}:
            raise ValueError("unsupported token header")
        expected = _b64e(hmac.new(settings.AUTH_SECRET.encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(signature, expected):
            raise ValueError("bad token signature")
        current_time = int(time.time()) if now is None else now
        if not isinstance(claims.get("exp"), int) or claims["exp"] <= current_time:
            raise ValueError("expired token")
        subject = claims.get("sub")
        if not isinstance(subject, str) or not subject:
            raise ValueError("missing token subject")
        return subject
    except (ValueError, TypeError, KeyError, json.JSONDecodeError, UnicodeDecodeError):
        raise HTTPException(status_code=401, detail={"code": "INVALID_TOKEN", "message": "Bearer token is invalid or expired"})


def get_authenticated_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> AuthenticatedUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail={"code": "AUTHENTICATION_REQUIRED", "message": "Bearer access token required"}, headers={"WWW-Authenticate": "Bearer"})
    user_id = _subject_from_token(credentials.credentials)
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=401, detail={"code": "ACCOUNT_NOT_FOUND", "message": "Account no longer exists"}, headers={"WWW-Authenticate": "Bearer"})
    return AuthenticatedUser(user_id=user.id, email=user.email, display_name=user.display_name, role=user.role)


def require_roles(*roles: str):
    def dependency(user: AuthenticatedUser = Depends(get_authenticated_user)) -> AuthenticatedUser:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail={"code": "FORBIDDEN", "message": "Insufficient role"})
        return user
    return dependency
