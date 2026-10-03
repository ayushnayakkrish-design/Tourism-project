from __future__ import annotations

import base64
import binascii

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.places import normalize_place, service as places_service
from app.config import settings
from app.core.auth import AuthenticatedUser, get_authenticated_user
from app.database import get_db
from app.dev3_models import UserPreference
from app.dev3_schemas import AudioInput, QueryInput
from app.services.intent import extract_intent_with_ai, google_maps_query

router = APIRouter()


def _require_voice(user: AuthenticatedUser, db: Session) -> UserPreference:
    preference = db.get(UserPreference, user.user_id)
    if preference is None:
        raise HTTPException(status_code=404, detail={"code": "PREFERENCES_NOT_FOUND", "message": "User preferences not found"})
    if not preference.voice_enabled:
        raise HTTPException(status_code=403, detail={"code": "VOICE_DISABLED", "message": "Voice queries are disabled in your preferences"})
    return preference


@router.post("/ai/intent")
async def parse_intent(data: QueryInput, _user: AuthenticatedUser = Depends(get_authenticated_user)):
    return await extract_intent_with_ai(data.text)


@router.post("/voice/query")
async def voice_query(data: QueryInput, user: AuthenticatedUser = Depends(get_authenticated_user), db: Session = Depends(get_db)):
    preference = _require_voice(user, db)
    return {"transcript": data.text, "language": preference.language, **(await extract_intent_with_ai(data.text))}


@router.post("/voice/transcribe")
async def transcribe(data: AudioInput, user: AuthenticatedUser = Depends(get_authenticated_user), db: Session = Depends(get_db)):
    preference = _require_voice(user, db)
    if not settings.SPEECH_TO_TEXT_API_URL or not settings.SPEECH_TO_TEXT_API_KEY:
        raise HTTPException(status_code=503, detail={"code": "SPEECH_PROVIDER_NOT_CONFIGURED", "message": "Speech-to-text provider is not configured"})
    try:
        audio = base64.b64decode(data.audio_base64, validate=True)
    except (binascii.Error, ValueError):
        raise HTTPException(status_code=422, detail={"code": "INVALID_AUDIO", "message": "audio_base64 must contain valid base64"})
    if not audio or len(audio) > 7_000_000:
        raise HTTPException(status_code=413, detail={"code": "AUDIO_TOO_LARGE", "message": "Audio must be smaller than 7 MB"})
    language = data.language or preference.language
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(settings.SPEECH_TO_TEXT_API_URL, json={"audio_base64": base64.b64encode(audio).decode("ascii"), "content_type": data.content_type, "language": language}, headers={"Authorization": f"Bearer {settings.SPEECH_TO_TEXT_API_KEY}"})
            response.raise_for_status()
            payload = response.json()
    except (httpx.HTTPError, ValueError):
        raise HTTPException(status_code=502, detail={"code": "SPEECH_PROVIDER_ERROR", "message": "Speech-to-text provider is unavailable or returned invalid data"})
    transcript = payload.get("transcript") if isinstance(payload, dict) else None
    if not isinstance(transcript, str) or not transcript.strip():
        raise HTTPException(status_code=502, detail={"code": "SPEECH_PROVIDER_ERROR", "message": "Speech-to-text provider returned no transcript"})
    return {"transcript": transcript.strip(), "language": language, **(await extract_intent_with_ai(transcript.strip()))}


@router.post("/voice/search")
async def voice_search(data: QueryInput, user: AuthenticatedUser = Depends(get_authenticated_user), db: Session = Depends(get_db)):
    _require_voice(user, db)
    intent = await extract_intent_with_ai(data.text)
    if intent["intent"] != "PLACE_SEARCH":
        return {"transcript": data.text, **intent, "places": []}
    parameters = intent["parameters"]
    query = parameters["category"] or "tourist attractions"
    if parameters["location"]:
        query += f" near {parameters['location']}"
    result = await places_service.search_text(query)
    return {"transcript": data.text, **intent, "places": [normalize_place(item) for item in result.get("places", [])], "integration_note": "open_now is extracted in intent; Developer 1's current PlacesService contract does not apply that filter"}


@router.get("/maps/query")
def maps_query(place_name: str, region: str | None = None):
    place_name = place_name.strip()
    if not place_name or len(place_name) > 200 or (region and len(region) > 120):
        raise HTTPException(status_code=422, detail={"code": "INVALID_MAPS_QUERY", "message": "place_name and region exceed their allowed lengths"})
    return google_maps_query(place_name, region)
