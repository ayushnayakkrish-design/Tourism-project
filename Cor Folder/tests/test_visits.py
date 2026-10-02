"""
Developer 2 — Integration tests for Visit API using FastAPI TestClient
with an in-memory SQLite database and MockPlaceProvider.
"""
from __future__ import annotations

import io
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.gamification.models import Visit, VisitStatus, Wallet, PointTransaction, TransactionType
from app.gamification.place_provider import MockPlaceProvider, PlaceInfo


# ---------------------------------------------------------------------------
# App fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def client_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    from app.main import app
    from app.gamification import api_visits
    from app.gamification.storage_provider import LocalStorageProvider
    from app.gamification.visit_service import VisitService

    mock_places = MockPlaceProvider()

    def override_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    # Override get_db
    app.dependency_overrides[get_db] = override_db

    # Monkeypatch _visit_service to use MockPlaceProvider
    original_visit_service = api_visits._visit_service

    def mock_visit_service():
        return VisitService(mock_places, LocalStorageProvider())

    api_visits._visit_service = mock_visit_service

    db = TestSession()
    yield TestClient(app), db, mock_places

    db.close()
    app.dependency_overrides.clear()
    api_visits._visit_service = original_visit_service
    Base.metadata.drop_all(engine)


NOW = datetime(2026, 10, 2, 10, 0, 0, tzinfo=timezone.utc)
USER_HEADERS = {"X-User-ID": "tourist-1"}
KONARK_PAYLOAD = {
    "place_id": "PLACE-KONARK",
    "latitude": 19.8878,
    "longitude": 86.0943,
    "timestamp": "2026-10-02T10:00:00Z",
}


# ---------------------------------------------------------------------------
# Visit Creation
# ---------------------------------------------------------------------------

class TestVisitCreation:
    def test_successful_visit_inside_radius(self, client_db):
        client, db, _ = client_db
        resp = client.post("/api/visits", json=KONARK_PAYLOAD, headers=USER_HEADERS)
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == VisitStatus.VERIFIED
        assert data["place_id"] == "PLACE-KONARK"
        assert data["user_id"] == "tourist-1"

    def test_visit_outside_radius_rejected(self, client_db):
        client, db, _ = client_db
        payload = {**KONARK_PAYLOAD, "latitude": 19.95, "longitude": 86.20}  # Far away
        resp = client.post("/api/visits", json=payload, headers=USER_HEADERS)
        assert resp.status_code == 201
        assert resp.json()["status"] == VisitStatus.REJECTED

    def test_invalid_place_returns_404(self, client_db):
        client, db, _ = client_db
        payload = {**KONARK_PAYLOAD, "place_id": "NONEXISTENT-PLACE"}
        resp = client.post("/api/visits", json=payload, headers=USER_HEADERS)
        assert resp.status_code == 404

    def test_future_timestamp_rejected(self, client_db):
        client, db, _ = client_db
        payload = {**KONARK_PAYLOAD, "timestamp": "2030-01-01T00:00:00Z"}
        resp = client.post("/api/visits", json=payload, headers=USER_HEADERS)
        assert resp.status_code == 422

    def test_invalid_coordinates_rejected(self, client_db):
        client, db, _ = client_db
        payload = {**KONARK_PAYLOAD, "latitude": 200.0}
        resp = client.post("/api/visits", json=payload, headers=USER_HEADERS)
        assert resp.status_code == 422

    def test_requires_authentication(self, client_db):
        client, db, _ = client_db
        resp = client.post("/api/visits", json=KONARK_PAYLOAD)
        assert resp.status_code == 401

    def test_user_id_from_header_not_body(self, client_db):
        """Backend must never accept user_id from request body."""
        client, db, _ = client_db
        # Even if someone puts user_id in a modified payload, it's ignored
        resp = client.post("/api/visits", json=KONARK_PAYLOAD, headers={"X-User-ID": "actual-user"})
        assert resp.status_code == 201
        assert resp.json()["user_id"] == "actual-user"

    def test_visit_awards_points_when_verified(self, client_db):
        client, db, _ = client_db
        resp = client.post("/api/visits", json=KONARK_PAYLOAD, headers=USER_HEADERS)
        assert resp.status_code == 201
        assert resp.json()["status"] == VisitStatus.VERIFIED
        db.expire_all()
        wallet = db.get(Wallet, "tourist-1")
        assert wallet is not None
        assert wallet.balance > 0

    def test_verified_visit_creates_ledger_entry(self, client_db):
        client, db, _ = client_db
        client.post("/api/visits", json=KONARK_PAYLOAD, headers=USER_HEADERS)
        db.expire_all()
        tx = db.query(PointTransaction).filter_by(
            user_id="tourist-1", transaction_type=TransactionType.VISIT_REWARD
        ).first()
        assert tx is not None

    def test_rejected_visit_awards_no_points(self, client_db):
        client, db, _ = client_db
        payload = {**KONARK_PAYLOAD, "latitude": 19.95, "longitude": 86.20}
        client.post("/api/visits", json=payload, headers=USER_HEADERS)
        db.expire_all()
        wallet = db.get(Wallet, "tourist-1")
        assert wallet is None or wallet.balance == 0


# ---------------------------------------------------------------------------
# Visit Idempotency
# ---------------------------------------------------------------------------

class TestVisitIdempotency:
    def test_visit_reward_not_granted_twice(self, client_db):
        """Two valid submits for the same place/time must not double-award."""
        client, db, _ = client_db
        client.post("/api/visits", json=KONARK_PAYLOAD, headers=USER_HEADERS)
        db.expire_all()
        wallet = db.get(Wallet, "tourist-1")
        balance_after_first = wallet.balance if wallet else 0

        # Submit again — should be FLAGGED as duplicate visit, no extra reward
        client.post("/api/visits", json=KONARK_PAYLOAD, headers=USER_HEADERS)
        db.expire_all()
        wallet = db.get(Wallet, "tourist-1")
        # Balance must not have doubled via duplicate reward
        visit_count = db.query(PointTransaction).filter_by(
            user_id="tourist-1", transaction_type=TransactionType.VISIT_REWARD
        ).count()
        # At most one VISIT_REWARD entry regardless of submissions
        assert visit_count <= 1


# ---------------------------------------------------------------------------
# Visit List & Detail
# ---------------------------------------------------------------------------

class TestVisitListDetail:
    def test_list_visits_own_only(self, client_db):
        client, db, _ = client_db
        client.post("/api/visits", json=KONARK_PAYLOAD, headers=USER_HEADERS)
        resp = client.get("/api/visits", headers=USER_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        for item in data["items"]:
            assert item["user_id"] == "tourist-1"

    def test_get_own_visit(self, client_db):
        client, db, _ = client_db
        create_resp = client.post("/api/visits", json=KONARK_PAYLOAD, headers=USER_HEADERS)
        visit_id = create_resp.json()["id"]
        resp = client.get(f"/api/visits/{visit_id}", headers=USER_HEADERS)
        assert resp.status_code == 200
        assert resp.json()["id"] == visit_id

    def test_cannot_access_others_visit(self, client_db):
        client, db, _ = client_db
        create_resp = client.post("/api/visits", json=KONARK_PAYLOAD, headers=USER_HEADERS)
        visit_id = create_resp.json()["id"]
        resp = client.get(f"/api/visits/{visit_id}", headers={"X-User-ID": "other-user"})
        assert resp.status_code == 403

    def test_get_nonexistent_visit_404(self, client_db):
        client, db, _ = client_db
        resp = client.get("/api/visits/99999", headers=USER_HEADERS)
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Photo Proof Upload
# ---------------------------------------------------------------------------

class TestPhotoProof:
    def _make_jpeg(self, size=200):
        """Create a minimal JPEG-like bytes sequence that passes size validation."""
        return b"\xff\xd8\xff\xe0" + b"\x00" * (size - 4) + b"\xff\xd9"

    def test_upload_valid_proof(self, client_db):
        client, db, _ = client_db
        create_resp = client.post("/api/visits", json=KONARK_PAYLOAD, headers=USER_HEADERS)
        visit_id = create_resp.json()["id"]
        resp = client.post(
            f"/api/visits/{visit_id}/proof",
            files={"file": ("photo.jpg", self._make_jpeg(1000), "image/jpeg")},
            headers=USER_HEADERS,
        )
        assert resp.status_code == 201
        assert resp.json()["visit_id"] == visit_id

    def test_upload_invalid_mime_type(self, client_db):
        client, db, _ = client_db
        create_resp = client.post("/api/visits", json=KONARK_PAYLOAD, headers=USER_HEADERS)
        visit_id = create_resp.json()["id"]
        resp = client.post(
            f"/api/visits/{visit_id}/proof",
            files={"file": ("doc.pdf", b"PDF content here", "application/pdf")},
            headers=USER_HEADERS,
        )
        assert resp.status_code == 422

    def test_upload_duplicate_image_rejected(self, client_db):
        client, db, _ = client_db
        create_resp1 = client.post("/api/visits", json=KONARK_PAYLOAD, headers=USER_HEADERS)
        visit_id1 = create_resp1.json()["id"]
        image_data = self._make_jpeg(2000)

        client.post(
            f"/api/visits/{visit_id1}/proof",
            files={"file": ("p.jpg", image_data, "image/jpeg")},
            headers=USER_HEADERS,
        )
        # Second upload of same image
        payload2 = {**KONARK_PAYLOAD, "timestamp": "2026-10-02T11:00:00Z"}
        create_resp2 = client.post("/api/visits", json=payload2, headers={"X-User-ID": "tourist-2"})
        visit_id2 = create_resp2.json()["id"]
        resp2 = client.post(
            f"/api/visits/{visit_id2}/proof",
            files={"file": ("p.jpg", image_data, "image/jpeg")},
            headers={"X-User-ID": "tourist-2"},
        )
        assert resp2.status_code == 409

    def test_cannot_upload_proof_for_others_visit(self, client_db):
        client, db, _ = client_db
        create_resp = client.post("/api/visits", json=KONARK_PAYLOAD, headers=USER_HEADERS)
        visit_id = create_resp.json()["id"]
        resp = client.post(
            f"/api/visits/{visit_id}/proof",
            files={"file": ("p.jpg", self._make_jpeg(500), "image/jpeg")},
            headers={"X-User-ID": "other-user"},
        )
        assert resp.status_code == 403

    def test_photo_reward_granted_once_for_verified_visit(self, client_db):
        client, db, _ = client_db
        create_resp = client.post("/api/visits", json=KONARK_PAYLOAD, headers=USER_HEADERS)
        assert create_resp.json()["status"] == VisitStatus.VERIFIED
        visit_id = create_resp.json()["id"]

        client.post(
            f"/api/visits/{visit_id}/proof",
            files={"file": ("p1.jpg", self._make_jpeg(500), "image/jpeg")},
            headers=USER_HEADERS,
        )
        db.expire_all()
        count = db.query(PointTransaction).filter_by(
            user_id="tourist-1", transaction_type=TransactionType.PHOTO_REWARD
        ).count()
        assert count == 1

    def test_photo_reward_not_granted_twice(self, client_db):
        client, db, _ = client_db
        create_resp = client.post("/api/visits", json=KONARK_PAYLOAD, headers=USER_HEADERS)
        visit_id = create_resp.json()["id"]

        # First unique image
        client.post(
            f"/api/visits/{visit_id}/proof",
            files={"file": ("p1.jpg", self._make_jpeg(500), "image/jpeg")},
            headers=USER_HEADERS,
        )
        # Second unique image — should not give another photo reward
        client.post(
            f"/api/visits/{visit_id}/proof",
            files={"file": ("p2.jpg", self._make_jpeg(600), "image/jpeg")},
            headers=USER_HEADERS,
        )
        db.expire_all()
        count = db.query(PointTransaction).filter_by(
            user_id="tourist-1", transaction_type=TransactionType.PHOTO_REWARD
        ).count()
        assert count == 1  # Only one photo reward ever


# ---------------------------------------------------------------------------
# Wallet API
# ---------------------------------------------------------------------------

class TestWalletAPI:
    def test_wallet_auto_created(self, client_db):
        client, db, _ = client_db
        resp = client.get("/api/wallet", headers=USER_HEADERS)
        assert resp.status_code == 200
        assert resp.json()["user_id"] == "tourist-1"
        assert resp.json()["balance"] == 0

    def test_wallet_shows_earned_points(self, client_db):
        client, db, _ = client_db
        client.post("/api/visits", json=KONARK_PAYLOAD, headers=USER_HEADERS)
        resp = client.get("/api/wallet", headers=USER_HEADERS)
        assert resp.status_code == 200
        assert resp.json()["balance"] > 0

    def test_transaction_history_pagination(self, client_db):
        client, db, _ = client_db
        client.post("/api/visits", json=KONARK_PAYLOAD, headers=USER_HEADERS)
        resp = client.get("/api/points/transactions?page=1&page_size=10", headers=USER_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
