from __future__ import annotations

import json
import re
from urllib.parse import quote_plus

import httpx
from pydantic import BaseModel, Field, ValidationError
from fastapi import HTTPException

from app.config import settings
from app.services.ai_service import AIService
from app.services.maps.base import request_with_retries


INTENTS = ("PLACE_SEARCH", "NEARBY_SEARCH", "ROUTE_REQUEST", "ITINERARY_REQUEST", "CROWD_QUERY", "BEST_TIME_QUERY", "PLACE_INFORMATION", "REWARD_QUERY", "COMMUNITY_SEARCH", "UNKNOWN")


class IntentParameters(BaseModel):
    category: str | None = None
    location: str | None = None
    open_now: bool = False
    query: str = Field(min_length=1, max_length=1000)


class IntentResult(BaseModel):
    intent: str
    parameters: IntentParameters

    @classmethod
    def validate_intent(cls, data: dict, original_query: str) -> dict:
        result = cls.model_validate(data)
        if result.intent not in INTENTS:
            raise ValueError("unsupported intent")
        if result.parameters.query != original_query:
            result.parameters.query = original_query
        if result.parameters.category and len(result.parameters.category) > 80:
            raise ValueError("category too long")
        if result.parameters.location and len(result.parameters.location) > 120:
            raise ValueError("location too long")
        return result.model_dump()

CATEGORY_TERMS = {
    "temple": ("temple", "temples", "mandir"),
    "beach": ("beach", "beaches"),
    "restaurant": ("restaurant", "restaurants", "food", "eat"),
    "hotel": ("hotel", "hotels", "stay", "accommodation"),
    "nature": ("nature", "park", "parks", "wildlife", "waterfall"),
}


def extract_intent(text: str) -> dict:
    normalized = text.casefold()
    category = next((name for name, words in CATEGORY_TERMS.items() if any(re.search(rf"\b{re.escape(word)}\b", normalized) for word in words)), None)
    location = None
    match = re.search(r"\b(?:near|in|around|at)\s+([\w][\w .'-]{0,60}?)(?:\s+(?:that|which|and|open|show|with|for)\b|[?.!,]|$)", text, re.I)
    if match:
        location = match.group(1).strip()
    if re.search(r"\b(itinerary|plan my trip|plan a trip|tour plan)\b", normalized):
        kind = "ITINERARY_REQUEST"
    elif re.search(r"\b(route|directions|how do i get|how to reach|way to)\b", normalized):
        kind = "ROUTE_REQUEST"
    elif re.search(r"\b(best time|when should i visit|least crowded)\b", normalized):
        kind = "BEST_TIME_QUERY"
    elif re.search(r"\b(crowd|crowded|busy|busiest)\b", normalized):
        kind = "CROWD_QUERY"
    elif re.search(r"\b(points|wallet|reward|rewards|redeem)\b", normalized):
        kind = "REWARD_QUERY"
    elif re.search(r"\b(community|local recommendation|locals recommend)\b", normalized):
        kind = "COMMUNITY_SEARCH"
    elif category or location:
        kind = "PLACE_SEARCH"
    elif re.search(r"\b(about|information|details|tell me)\b", normalized):
        kind = "PLACE_INFORMATION"
    else:
        kind = "UNKNOWN"
    return {
        "intent": kind,
    "parameters": {
            "category": category,
            "location": location,
            "open_now": bool(re.search(r"\b(open now|open right now|currently open)\b", normalized)),
            "query": text.strip(),
        },
    }


async def extract_intent_with_ai(text: str) -> dict:
    """Use strict structured extraction when configured; otherwise use local rules."""
    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY.startswith("optional_") or settings.OPENAI_API_KEY.startswith("your_"):
        return extract_intent(text)
    schema = {
        "type": "object",
        "properties": {
            "intent": {"type": "string", "enum": list(INTENTS)},
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {"type": ["string", "null"], "enum": ["temple", "beach", "restaurant", "hotel", "nature", None]},
                    "location": {"type": ["string", "null"]},
                    "open_now": {"type": "boolean"},
                    "query": {"type": "string"},
                },
                "required": ["category", "location", "open_now", "query"],
                "additionalProperties": False,
            },
        },
        "required": ["intent", "parameters"],
        "additionalProperties": False,
    }
    body = {
        "model": settings.OPENAI_MODEL,
        "input": "Extract only intent and query parameters from the user text. Do not answer the query or invent tourism facts. Preserve the original query exactly.\n\n" + text,
        "store": False,
        "text": {"format": {"type": "json_schema", "name": "tourism_query_intent", "strict": True, "schema": schema}},
    }
    try:
        async with httpx.AsyncClient(timeout=settings.OPENAI_TIMEOUT_SECONDS) as client:
            response = await request_with_retries(client, "POST", "https://api.openai.com/v1/responses", headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}", "Content-Type": "application/json"}, json_body=body, retries=settings.OPENAI_RETRIES, service="openai_intent")
        raw = AIService._extract_output_text(response.json())
        return IntentResult.validate_intent(json.loads(raw), text)
    except (HTTPException, httpx.HTTPError, ValueError, TypeError, ValidationError, KeyError):
        # Provider or schema failures use a deterministic, validated local parse.
        return extract_intent(text)


def google_maps_query(place_name: str, region: str | None = None) -> dict:
    query = " ".join(part.strip() for part in (place_name, region or "") if part and part.strip())
    return {"place_name": place_name, "google_maps_query": query, "url": "https://www.google.com/maps/search/?api=1&query=" + quote_plus(query)}
