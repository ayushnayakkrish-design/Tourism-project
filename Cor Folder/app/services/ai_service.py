import json

import httpx
from fastapi import HTTPException

from app.config import settings
from app.services.maps.base import request_with_retries

OPENAI_URL = "https://api.openai.com/v1/responses"


class AIService:
    async def explain_itinerary(self, itinerary: dict) -> dict:
        if not settings.OPENAI_API_KEY:
            return {
                "enabled": False,
                "explanation": "AI explanation is disabled. Set OPENAI_API_KEY to enable it.",
            }

        prompt = (
            "Explain the supplied tourism itinerary using ONLY the structured facts provided. "
            "Do not add or infer opening hours, crowd measurements, prices, distances, weather, "
            "ratings, travel times, or other factual tourism information. Return concise bullet points.\n\n"
            + json.dumps(itinerary, default=str, ensure_ascii=False)
        )
        body = {
            "model": settings.OPENAI_MODEL,
            "input": prompt,
            "store": False,
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "itinerary_explanation",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {"bullets": {"type": "array", "items": {"type": "string"}}},
                        "required": ["bullets"],
                        "additionalProperties": False,
                    },
                }
            },
        }
        headers = {
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=settings.OPENAI_TIMEOUT_SECONDS) as client:
            response = await request_with_retries(
                client,
                "POST",
                OPENAI_URL,
                headers=headers,
                json_body=body,
                retries=settings.OPENAI_RETRIES,
                service="openai",
            )

        payload = response.json()
        text = self._extract_output_text(payload)
        if not text:
            raise HTTPException(
                status_code=502,
                detail={"code": "OPENAI_EMPTY_RESPONSE", "message": "OpenAI returned no explanation"},
            )
        try:
            structured = json.loads(text)
            bullets = structured.get("bullets", [])
            if not isinstance(bullets, list) or not all(isinstance(x, str) for x in bullets):
                raise ValueError("invalid bullets")
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            raise HTTPException(
                status_code=502,
                detail={"code": "OPENAI_INVALID_RESPONSE", "message": "OpenAI returned an invalid structured explanation"},
            ) from exc

        return {"enabled": True, "explanation": bullets}

    @staticmethod
    def _extract_output_text(payload: dict) -> str:
        # The SDK exposes output_text as a convenience property; raw REST responses contain output items.
        direct = payload.get("output_text")
        if isinstance(direct, str) and direct.strip():
            return direct
        chunks = []
        for item in payload.get("output", []):
            for content in item.get("content", []) if isinstance(item, dict) else []:
                if content.get("type") in {"output_text", "text"} and isinstance(content.get("text"), str):
                    chunks.append(content["text"])
        return "\n".join(chunks).strip()
