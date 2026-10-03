"""
End-to-end multi-developer integration flow tests.

Verifies the 9 end-to-end integration flows uniting Developer 1, Developer 2, and Developer 3:
1. Registration -> Authentication -> CurrentUser Identity
2. Place discovery -> Visit creation -> GPS verification -> Visit reward granted
3. Visit -> Photo proof upload -> Proof verification -> Photo reward granted
4. Wallet balance -> Point transaction ledger integrity
5. Reward catalog -> Selection -> Atomic redemption -> Code generation -> Stock decrement
6. Admin reward management -> Modification -> Stock tracking -> Aggregate analytics
7. Community place submission -> Moderation approval -> Public visibility
8. Multilingual localization -> Translation service & caching
9. Developer 1 Places integration -> Developer 2 Visit verification
"""
from __future__ import annotations

import io
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database import Base, engine, SessionLocal, get_db
from app.core.passwords import hash_password
from app.dev3_models import User, UserPreference, TranslationCache


@pytest.fixture
def clean_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_complete_integrated_system_flows(clean_db):
    client = TestClient(app)

    # FLOW 1: Registration & Bearer Token Authentication
    r = client.post("/api/auth/register", json={
        "email": "tourist1@example.com",
        "password": "StrongPassword123!",
        "display_name": "Tourist One"
    })
    assert r.status_code == 201
    user_token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {user_token}"}

    r_me = client.get("/api/auth/me", headers=headers)
    assert r_me.status_code == 200
    assert r_me.json()["email"] == "tourist1@example.com"

    # Create Super Admin User
    with SessionLocal() as db:
        admin = User(
            id="admin_super_1",
            email="admin@example.com",
            password_hash=hash_password("AdminPassword123!"),
            display_name="Admin User",
            role="SUPER_ADMIN"
        )
        db.add(admin)
        db.add(UserPreference(user_id=admin.id))
        db.commit()

    r_admin_login = client.post("/api/auth/login", json={
        "email": "admin@example.com",
        "password": "AdminPassword123!"
    })
    assert r_admin_login.status_code == 200
    admin_token = r_admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # FLOW 2: Place discovery & GPS Visit verification
    visit_payload = {
        "place_id": "PLACE-KONARK",
        "latitude": 19.8876,
        "longitude": 86.0945,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    r_visit = client.post("/api/visits", json=visit_payload, headers=headers)
    assert r_visit.status_code == 201
    visit_data = r_visit.json()
    assert visit_data["status"] == "VERIFIED"
    assert visit_data["visit_reward_granted"] is True
    visit_id = visit_data["id"]

    # FLOW 3: Photo proof upload & photo reward granting
    fake_image = b"GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;" + b"A" * 200
    files = {"file": ("konark.png", io.BytesIO(fake_image), "image/png")}
    r_proof = client.post(f"/api/visits/{visit_id}/proof", files=files, headers=headers)
    assert r_proof.status_code == 201
    assert r_proof.json()["verification_status"] == "ACCEPTED"

    # FLOW 4: Wallet balance & transaction ledger
    r_wallet = client.get("/api/wallet", headers=headers)
    assert r_wallet.status_code == 200
    assert r_wallet.json()["balance"] == 60  # 50 visit + 10 photo

    r_tx = client.get("/api/points/transactions", headers=headers)
    assert r_tx.status_code == 200
    assert r_tx.json()["total"] == 2

    # FLOW 6: Admin creates reward with stock
    r_create_rew = client.post("/api/admin/rewards", json={
        "name": "Konark Souvenir Guidebook",
        "description": "Official guidebook with map",
        "provider": "Odisha Tourism",
        "category": "souvenir",
        "points_required": 40,
        "stock": 5
    }, headers=admin_headers)
    assert r_create_rew.status_code == 201
    reward_id = r_create_rew.json()["id"]

    # FLOW 5: Reward browsing & atomic redemption
    r_catalog = client.get("/api/rewards", headers=headers)
    assert r_catalog.status_code == 200
    assert r_catalog.json()["total"] >= 1

    r_redeem = client.post(f"/api/rewards/{reward_id}/redeem", headers=headers)
    assert r_redeem.status_code == 201
    redemption_code = r_redeem.json()["redemption_code"]
    assert redemption_code.startswith("TRV-")

    # Verify wallet deduction (60 - 40 = 20)
    r_wallet2 = client.get("/api/wallet", headers=headers)
    assert r_wallet2.json()["balance"] == 20

    # Verify stock decrement (5 - 1 = 4)
    r_rew_check = client.get(f"/api/rewards/{reward_id}", headers=headers)
    assert r_rew_check.json()["stock"] == 4

    # Admin analytics inspection
    r_analytics = client.get("/api/admin/reward-analytics", headers=admin_headers)
    assert r_analytics.status_code == 200
    assert r_analytics.json()["total_redemptions"] >= 1

    # FLOW 7: Community submission & Moderation workflow
    r_sub = client.post("/api/community/places", json={
        "type": "restaurant",
        "name": "Puri Coastal Dhaba",
        "latitude": 19.7983,
        "longitude": 85.8249,
        "description": "Great authentic seafood near the golden beach.",
        "photos": ["https://example.com/dhaba.jpg"],
        "language": "en"
    }, headers=headers)
    assert r_sub.status_code == 201
    sub_id = r_sub.json()["id"]
    assert r_sub.json()["status"] == "PENDING"

    r_app = client.post(f"/api/moderation/submissions/{sub_id}/approve", json={"note": "Approved by moderation team"}, headers=admin_headers)
    assert r_app.status_code == 200
    assert r_app.json()["status"] == "APPROVED"

    r_public = client.get("/api/community/places")
    assert r_public.status_code == 200
    assert any(s["id"] == sub_id for s in r_public.json())

    # FLOW 8: Localization & Translation Cache
    with SessionLocal() as db:
        db.add(TranslationCache(
            cache_key=__import__("hashlib").sha256(b"en\x00hi\x00Namaste India").hexdigest(),
            translation="\u0928\u092e\u0938\u094d\u0924\u0947 \u092d\u093e\u0930\u0924"
        ))
        db.commit()

    r_trans = client.post("/api/translate", json={
        "text": "Namaste India",
        "source_language": "en",
        "target_language": "hi"
    }, headers=headers)
    assert r_trans.status_code == 200
    assert r_trans.json()["cached"] is True

    # FLOW 9: Dev 1 Place -> Dev 2 Visit verification
    r_reg2 = client.post("/api/auth/register", json={
        "email": "tourist2@example.com",
        "password": "StrongPassword123!",
        "display_name": "Tourist Two"
    })
    tok2 = r_reg2.json()["access_token"]
    headers2 = {"Authorization": f"Bearer {tok2}"}

    r_visit_taj = client.post("/api/visits", json={
        "place_id": "PLACE-TAJMAHAL",
        "latitude": 27.1751,
        "longitude": 78.0421,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }, headers=headers2)
    assert r_visit_taj.status_code == 201
    assert r_visit_taj.json()["status"] == "VERIFIED"
    assert r_visit_taj.json()["distance_from_place"] < 10.0
    assert r_visit_taj.json()["visit_reward_granted"] is True
