import asyncio
import json
from typing import Any

import httpx
from fastapi import HTTPException

from app.config import settings


def _safe_error_detail(service: str, response: httpx.Response) -> dict[str, Any]:
    detail = "Upstream service request failed"
    try:
        payload = response.json()
        if isinstance(payload, dict):
            detail = payload.get("error", {}).get("message") or payload.get("message") or detail
    except (ValueError, json.JSONDecodeError):
        pass
    return {
        "code": f"{service.upper()}_UPSTREAM_ERROR",
        "message": detail[:500],
        "upstream_status": response.status_code,
    }


async def request_with_retries(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    *,
    headers: dict[str, str],
    json_body: dict | None = None,
    retries: int,
    service: str,
):
    last_response = None
    for attempt in range(retries + 1):
        try:
            response = await client.request(method, url, headers=headers, json=json_body)
        except httpx.TimeoutException as exc:
            if attempt >= retries:
                raise HTTPException(
                    status_code=504,
                    detail={"code": f"{service.upper()}_TIMEOUT", "message": "Upstream service timed out"},
                ) from exc
            await asyncio.sleep(0.25 * (2**attempt))
            continue
        except httpx.RequestError as exc:
            if attempt >= retries:
                raise HTTPException(
                    status_code=502,
                    detail={"code": f"{service.upper()}_NETWORK_ERROR", "message": "Could not reach upstream service"},
                ) from exc
            await asyncio.sleep(0.25 * (2**attempt))
            continue

        last_response = response
        if response.status_code < 400:
            return response
        if response.status_code in {408, 429} or response.status_code >= 500:
            if attempt < retries:
                await asyncio.sleep(0.25 * (2**attempt))
                continue
        raise HTTPException(status_code=502 if response.status_code >= 500 else 400, detail=_safe_error_detail(service, response))

    raise HTTPException(
        status_code=502,
        detail={"code": f"{service.upper()}_UPSTREAM_ERROR", "message": "Upstream service request failed"},
    )
