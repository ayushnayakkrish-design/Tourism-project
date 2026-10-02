import json

import pytest

from app.services.maps.routes_service import RoutesService


@pytest.mark.asyncio
async def test_compute_matrix_parses_ndjson(monkeypatch):
    service = RoutesService()
    service.api_key = "test-key"

    class Response:
        status_code = 200
        text = json.dumps({"originIndex": 0, "destinationIndex": 1, "status": {"code": 0}, "condition": "ROUTE_EXISTS", "duration": "120s"}) + "\n" + json.dumps({"originIndex": 1, "destinationIndex": 0, "status": {"code": 0}, "condition": "ROUTE_EXISTS", "duration": "100s"})

        def json(self):
            raise ValueError("NDJSON")

    class Client:
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            pass

    async def fake_request(*args, **kwargs):
        return Response()

    monkeypatch.setattr("app.services.maps.routes_service.httpx.AsyncClient", lambda *args, **kwargs: Client())
    monkeypatch.setattr("app.services.maps.routes_service.request_with_retries", fake_request)
    result = await service.compute_matrix([{"latitude": 1, "longitude": 2}], [{"latitude": 3, "longitude": 4}])
    assert len(result) == 2
    assert result[0]["duration"] == "120s"
