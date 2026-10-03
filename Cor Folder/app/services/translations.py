from __future__ import annotations

import hashlib

import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.dev3_models import TranslationCache


def translate_text(db: Session, text: str, source_language: str, target_language: str) -> tuple[str, bool]:
    if source_language == target_language:
        return text, True
    cache_key = hashlib.sha256(f"{source_language}\0{target_language}\0{text}".encode("utf-8")).hexdigest()
    cached = db.get(TranslationCache, cache_key)
    if cached is not None:
        return cached.translation, True
    if not settings.TRANSLATION_API_URL or not settings.TRANSLATION_API_KEY:
        raise HTTPException(status_code=503, detail={"code": "TRANSLATION_NOT_CONFIGURED", "message": "Translation provider is not configured"})
    try:
        response = httpx.post(settings.TRANSLATION_API_URL, json={"text": text, "source_language": source_language, "target_language": target_language}, headers={"Authorization": f"Bearer {settings.TRANSLATION_API_KEY}"}, timeout=20)
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError):
        raise HTTPException(status_code=502, detail={"code": "TRANSLATION_PROVIDER_ERROR", "message": "Translation provider is unavailable or returned invalid data"})
    translated = payload.get("translation") if isinstance(payload, dict) else None
    if not isinstance(translated, str) or not translated.strip():
        raise HTTPException(status_code=502, detail={"code": "TRANSLATION_PROVIDER_ERROR", "message": "Translation provider returned no translation"})
    translated = translated.strip()
    db.add(TranslationCache(cache_key=cache_key, translation=translated))
    db.commit()
    return translated, False
