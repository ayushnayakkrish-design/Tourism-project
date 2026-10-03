from __future__ import annotations

from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.dev3_models import ModerationAction, User


@pytest.fixture
def api():
    from app.main import app

    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    test_session = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    def override_db():
        db = test_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    db = test_session()
    with TestClient(app) as client:
        yield client, db
    db.close()
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)
    engine.dispose()


def register(client: TestClient, email: str = "tourist@example.com") -> tuple[dict, dict]:
    response = client.post("/api/auth/register", json={"email": email, "password": "CorrectHorse7!", "display_name": "Tourist"})
    assert response.status_code == 201, response.text
    body = response.json()
    return body, {"Authorization": f"Bearer {body['access_token']}"}


def test_auth_profile_preferences_and_d2_bearer_integration(api):
    client, _db = api
    body, headers = register(client)
    assert body["user"]["role"] == "TOURIST"
    assert "password_hash" not in body["user"]
    assert client.get("/api/auth/me", headers=headers).json()["email"] == "tourist@example.com"

    preferences_url = "/api/users/me/preferences"
    assert client.get(preferences_url, headers=headers).json() == {"language": "en", "theme": "system", "voice_enabled": True, "units": "metric"}
    updated = client.patch(preferences_url, json={"language": "or", "voice_enabled": False}, headers=headers)
    assert updated.status_code == 200
    assert updated.json()["language"] == "or"
    assert client.get(preferences_url, headers=headers).json()["voice_enabled"] is False
    assert client.patch(preferences_url, json={"language": "fr"}, headers=headers).status_code == 422

    # Developer 2's existing interface now gets the authenticated stable user ID.
    wallet = client.get("/api/wallet", headers=headers)
    assert wallet.status_code == 200
    assert wallet.json()["user_id"] == body["user"]["id"]
    assert client.get("/api/wallet", headers={"X-User-ID": "forged-user"}).status_code == 401


def test_registration_duplicate_and_bad_credentials(api):
    client, _db = api
    register(client)
    duplicate = client.post("/api/auth/register", json={"email": "TOURIST@example.com", "password": "CorrectHorse7!", "display_name": "Again"})
    assert duplicate.status_code == 409
    assert client.post("/api/auth/login", json={"email": "tourist@example.com", "password": "wrong-password"}).status_code == 401
    assert client.get("/api/users/me/preferences", headers={"X-User-ID": "forged-user"}).status_code == 401


def test_submission_review_moderation_and_audit(api):
    client, db = api
    body, headers = register(client)
    submitted = client.post("/api/community/places", json={
        "type": "temple", "name": "Local Temple", "latitude": 19.8, "longitude": 85.8,
        "description": "A community submitted place with enough detail.", "language": "en", "photos": [],
    }, headers=headers)
    assert submitted.status_code == 201
    submission_id = submitted.json()["id"]
    assert submitted.json()["status"] == "PENDING"
    assert client.get("/api/community/places").json() == []
    assert client.get("/api/community/places/mine", headers=headers).json()[0]["id"] == submission_id
    assert client.get("/api/moderation/queue", headers=headers).status_code == 403

    review = client.post("/api/community/reviews", json={"place_id": "CHIJopaque", "rating": 5, "comment": "Lovely"}, headers=headers)
    assert review.status_code == 201
    assert review.json()["status"] == "PENDING"
    assert client.post("/api/community/reviews", json={"place_id": "CHIJopaque", "rating": 4}, headers=headers).status_code == 409
    assert client.get("/api/places/CHIJopaque/reviews").json() == []

    user = db.get(User, body["user"]["id"])
    user.role = "SUPER_ADMIN"
    db.commit()
    assert client.get("/api/moderation/queue", headers=headers).status_code == 200
    decision = client.post(f"/api/moderation/submissions/{submission_id}/approve", json={"note": "Reviewed"}, headers=headers)
    assert decision.status_code == 200
    assert decision.json()["status"] == "APPROVED"
    assert client.get("/api/community/places").json()[0]["id"] == submission_id
    assert db.query(ModerationAction).filter_by(target_id=submission_id, action="APPROVED").count() == 1
    history = client.get(f"/api/moderation/history?target_type=submission&target_id={submission_id}", headers=headers)
    assert history.status_code == 200
    assert history.json()[0]["action"] == "APPROVED"


def test_translation_cache_and_voice_intent(api, monkeypatch):
    client, _db = api
    _body, headers = register(client)

    import app.services.translations as translations
    monkeypatch.setattr(translations.settings, "TRANSLATION_API_URL", "https://provider.invalid/translate")
    monkeypatch.setattr(translations.settings, "TRANSLATION_API_KEY", "test-key")
    mocked_response = Mock()
    mocked_response.json.return_value = {"translation": "କୋଣାର୍କ ସ୍ୱାଗତ"}
    mocked_response.raise_for_status.return_value = None
    mocked_post = Mock(return_value=mocked_response)
    monkeypatch.setattr(translations.httpx, "post", mocked_post)
    payload = {"text": "Welcome to Konark", "source_language": "en", "target_language": "or"}
    first = client.post("/api/translate", json=payload, headers=headers)
    second = client.post("/api/translate", json=payload, headers=headers)
    assert first.json()["cached"] is False
    assert second.json()["cached"] is True
    assert mocked_post.call_count == 1

    voice = client.post("/api/voice/query", json={"text": "Show temples near Puri that are open now"}, headers=headers)
    assert voice.status_code == 200
    assert voice.json()["intent"] == "PLACE_SEARCH"
    assert voice.json()["parameters"] == {"category": "temple", "location": "Puri", "open_now": True, "query": "Show temples near Puri that are open now"}

    import app.api.voice as voice_api
    async def fake_search(query: str, max_result_count: int = 10):
        return {"places": [{"id": "places/puri-temple", "displayName": {"text": "Temple"}, "location": {"latitude": 19.8, "longitude": 85.8}}]}
    monkeypatch.setattr(voice_api.places_service, "search_text", fake_search)
    search = client.post("/api/voice/search", json={"text": "Show temples near Puri"}, headers=headers)
    assert search.status_code == 200
    assert search.json()["places"][0]["place_id"] == "places/puri-temple"
    assert client.get("/api/maps/query", params={"place_name": "Konark Sun Temple", "region": "Odisha"}, headers=headers).json()["google_maps_query"] == "Konark Sun Temple Odisha"
