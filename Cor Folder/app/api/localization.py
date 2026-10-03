from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.auth import AuthenticatedUser, get_authenticated_user, require_roles
from app.database import get_db
from app.dev3_models import PlaceContent
from app.dev3_schemas import PlaceContentInput, TranslateInput
from app.services.translations import translate_text

router = APIRouter()
translation_router = APIRouter()


@router.get("/{place_id}/content/{language}")
def get_place_content(place_id: str, language: str, db: Session = Depends(get_db)):
    row = db.query(PlaceContent).filter_by(place_id=place_id, language=language).first()
    if row is None:
        raise HTTPException(status_code=404, detail={"code": "LOCALIZED_CONTENT_NOT_FOUND", "message": "No content for this place and language"})
    return {"place_id": row.place_id, "language": row.language, "title": row.title, "description": row.description, "rules": row.rules, "tips": row.tips, "source": row.source, "updated_at": row.updated_at}


@router.put("/{place_id}/content/{language}")
def put_place_content(place_id: str, language: str, data: PlaceContentInput, user: AuthenticatedUser = Depends(require_roles("MODERATOR", "GOVERNMENT_ADMIN", "SUPER_ADMIN")), db: Session = Depends(get_db)):
    if data.language != language:
        raise HTTPException(status_code=422, detail={"code": "CONTENT_PATH_MISMATCH", "message": "Path language must match the body"})
    if data.source == "official" and user.role not in {"GOVERNMENT_ADMIN", "SUPER_ADMIN"}:
        raise HTTPException(status_code=403, detail={"code": "FORBIDDEN", "message": "Only government administrators may publish official content"})
    row = db.query(PlaceContent).filter_by(place_id=place_id, language=language).first()
    if row is None:
        row = PlaceContent(id=secrets.token_urlsafe(18), place_id=place_id, language=language, **data.model_dump())
        db.add(row)
    else:
        for key, value in data.model_dump().items():
            setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return {"place_id": row.place_id, "language": row.language, "title": row.title, "description": row.description, "rules": row.rules, "tips": row.tips, "source": row.source, "updated_at": row.updated_at}


@translation_router.post("/translate")
def translate(data: TranslateInput, _user: AuthenticatedUser = Depends(get_authenticated_user), db: Session = Depends(get_db)):
    translated, cached = translate_text(db, data.text, data.source_language, data.target_language)
    return {"translation": translated, "cached": cached, "source_language": data.source_language, "target_language": data.target_language}
