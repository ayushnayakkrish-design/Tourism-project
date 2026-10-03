from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.core.auth import AuthenticatedUser, create_access_token, get_authenticated_user
from app.core.passwords import hash_password, verify_password
from app.database import get_db
from app.dev3_models import User, UserPreference
from app.dev3_schemas import LoginInput, RegisterInput

router = APIRouter()


def public_user(user: User) -> dict:
    return {"id": user.id, "email": user.email, "display_name": user.display_name, "bio": user.bio, "role": user.role}


def token_response(user: User) -> dict:
    return {"access_token": create_access_token(user), "token_type": "bearer", "expires_in": settings.ACCESS_TOKEN_MINUTES * 60, "user": public_user(user)}


@router.post("/register", status_code=201)
def register(data: RegisterInput, db: Session = Depends(get_db)):
    user = User(id=secrets.token_urlsafe(18), email=data.email, password_hash=hash_password(data.password), display_name=data.display_name)
    try:
        db.add(user)
        db.flush()
        db.add(UserPreference(user_id=user.id))
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail={"code": "ACCOUNT_EXISTS", "message": "An account with this email already exists"})
    return token_response(user)


@router.post("/login")
def login(data: LoginInput, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if user is None or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail={"code": "INVALID_CREDENTIALS", "message": "Email or password is incorrect"}, headers={"WWW-Authenticate": "Bearer"})
    return token_response(user)


@router.get("/me")
def me(user: AuthenticatedUser = Depends(get_authenticated_user), db: Session = Depends(get_db)):
    record = db.get(User, user.user_id)
    return public_user(record)
