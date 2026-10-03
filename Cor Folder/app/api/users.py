from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import AuthenticatedUser, get_authenticated_user, require_roles
from app.database import get_db
from app.dev3_models import ModerationAction, User, UserPreference
from app.dev3_schemas import PreferencesPatch, ProfilePatch, RolePatch
from app.api.auth import public_user

router = APIRouter()
admin_router = APIRouter()


def _preference_response(preference: UserPreference) -> dict:
    return {"language": preference.language, "theme": preference.theme, "voice_enabled": preference.voice_enabled, "units": preference.units}


@router.get("/me")
def get_profile(user: AuthenticatedUser = Depends(get_authenticated_user), db: Session = Depends(get_db)):
    record = db.get(User, user.user_id)
    if record is None:
        raise HTTPException(status_code=404, detail={"code": "USER_NOT_FOUND", "message": "User not found"})
    return public_user(record)


@router.patch("/me")
def patch_profile(data: ProfilePatch, user: AuthenticatedUser = Depends(get_authenticated_user), db: Session = Depends(get_db)):
    record = db.get(User, user.user_id)
    if record is None:
        raise HTTPException(status_code=404, detail={"code": "USER_NOT_FOUND", "message": "User not found"})
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(record, key, value)
    db.commit()
    db.refresh(record)
    return public_user(record)


@router.get("/me/preferences")
def get_preferences(user: AuthenticatedUser = Depends(get_authenticated_user), db: Session = Depends(get_db)):
    preference = db.get(UserPreference, user.user_id)
    if preference is None:
        raise HTTPException(status_code=404, detail={"code": "PREFERENCES_NOT_FOUND", "message": "User preferences not found"})
    return _preference_response(preference)


@router.patch("/me/preferences")
def patch_preferences(data: PreferencesPatch, user: AuthenticatedUser = Depends(get_authenticated_user), db: Session = Depends(get_db)):
    preference = db.get(UserPreference, user.user_id)
    if preference is None:
        raise HTTPException(status_code=404, detail={"code": "PREFERENCES_NOT_FOUND", "message": "User preferences not found"})
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(preference, key, value)
    db.commit()
    db.refresh(preference)
    return _preference_response(preference)


@admin_router.patch("/admin/users/{user_id}/role")
def update_role(user_id: str, data: RolePatch, admin: AuthenticatedUser = Depends(require_roles("SUPER_ADMIN")), db: Session = Depends(get_db)):
    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail={"code": "USER_NOT_FOUND", "message": "User not found"})
    target.role = data.role
    import secrets
    db.add(ModerationAction(id=secrets.token_urlsafe(18), moderator_id=admin.user_id, target_type="user_role", target_id=user_id, action=data.role, note="Role updated by super administrator"))
    db.commit()
    return {"user_id": user_id, "role": target.role}
