"""
Developer 2 — Integration tests for Rewards & Redemption using FastAPI TestClient
with an in-memory SQLite database.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.gamification.models import Reward, RewardStatus, Wallet, PointTransaction, TransactionType
from app.gamification.wallet_service import WalletService


# ---------------------------------------------------------------------------
# App fixture with overridden DB
# ---------------------------------------------------------------------------

@pytest.fixture
def client_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)

    from app.main import app

    def override_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_db
    db = TestSession()
    yield TestClient(app), db
    db.close()
    app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)


def _seed_reward(db, points_required=100, stock=10, status=RewardStatus.ACTIVE):
    r = Reward(
        name="Test Discount",
        description="Test reward",
        provider="TestCo",
        category="discount",
        points_required=points_required,
        stock=stock,
        status=status,
    )
    db.add(r)
    db.commit()
    db.refresh(r)
    return r


def _give_points(db, user_id, amount):
    svc = WalletService()
    svc.credit(db, user_id, amount, TransactionType.BONUS, description="Test credit")
    db.commit()


# ---------------------------------------------------------------------------
# Reward Catalog
# ---------------------------------------------------------------------------

class TestRewardCatalog:
    def test_list_rewards_empty(self, client_db):
        client, db = client_db
        resp = client.get("/api/rewards", headers={"X-User-ID": "user-1"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_list_rewards_returns_active(self, client_db):
        client, db = client_db
        _seed_reward(db)
        resp = client.get("/api/rewards", headers={"X-User-ID": "user-1"})
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_list_rewards_hides_inactive(self, client_db):
        client, db = client_db
        _seed_reward(db, status=RewardStatus.INACTIVE)
        resp = client.get("/api/rewards", headers={"X-User-ID": "user-1"})
        assert resp.json()["total"] == 0

    def test_list_rewards_filter_by_category(self, client_db):
        client, db = client_db
        _seed_reward(db)
        resp = client.get(
            "/api/rewards?category=discount", headers={"X-User-ID": "user-1"}
        )
        assert resp.json()["total"] == 1

    def test_list_rewards_filter_no_match(self, client_db):
        client, db = client_db
        _seed_reward(db)
        resp = client.get(
            "/api/rewards?category=hotel", headers={"X-User-ID": "user-1"}
        )
        assert resp.json()["total"] == 0

    def test_get_reward_by_id(self, client_db):
        client, db = client_db
        r = _seed_reward(db)
        resp = client.get(f"/api/rewards/{r.id}", headers={"X-User-ID": "user-1"})
        assert resp.status_code == 200
        assert resp.json()["id"] == r.id

    def test_get_nonexistent_reward_404(self, client_db):
        client, db = client_db
        resp = client.get("/api/rewards/9999", headers={"X-User-ID": "user-1"})
        assert resp.status_code == 404

    def test_requires_auth(self, client_db):
        client, db = client_db
        resp = client.get("/api/rewards")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Redemption
# ---------------------------------------------------------------------------

class TestRedemption:
    def test_successful_redemption(self, client_db):
        client, db = client_db
        r = _seed_reward(db, points_required=100, stock=5)
        _give_points(db, "user-1", 200)
        resp = client.post(
            f"/api/rewards/{r.id}/redeem",
            headers={"X-User-ID": "user-1"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["reward_id"] == r.id
        assert data["status"] == "ACTIVE"
        assert data["redemption_code"].startswith("TRV-")

    def test_redemption_deducts_points(self, client_db):
        client, db = client_db
        r = _seed_reward(db, points_required=50)
        _give_points(db, "user-1", 100)
        client.post(f"/api/rewards/{r.id}/redeem", headers={"X-User-ID": "user-1"})
        db.expire_all()
        wallet = db.get(Wallet, "user-1")
        assert wallet.balance == 50

    def test_redemption_decrements_stock(self, client_db):
        client, db = client_db
        r = _seed_reward(db, points_required=50, stock=2)
        _give_points(db, "user-1", 200)
        client.post(f"/api/rewards/{r.id}/redeem", headers={"X-User-ID": "user-1"})
        db.expire_all()
        r_fresh = db.get(Reward, r.id)
        assert r_fresh.stock == 1

    def test_insufficient_points_fails(self, client_db):
        client, db = client_db
        r = _seed_reward(db, points_required=500)
        _give_points(db, "user-1", 100)
        resp = client.post(
            f"/api/rewards/{r.id}/redeem",
            headers={"X-User-ID": "user-1"},
        )
        assert resp.status_code == 422
        assert resp.json()["detail"]["code"] == "INSUFFICIENT_POINTS"

    def test_out_of_stock_fails(self, client_db):
        client, db = client_db
        r = _seed_reward(db, points_required=50, stock=0, status=RewardStatus.OUT_OF_STOCK)
        _give_points(db, "user-1", 200)
        resp = client.post(
            f"/api/rewards/{r.id}/redeem",
            headers={"X-User-ID": "user-1"},
        )
        assert resp.status_code == 422

    def test_inactive_reward_fails(self, client_db):
        client, db = client_db
        r = _seed_reward(db, status=RewardStatus.INACTIVE)
        _give_points(db, "user-1", 200)
        resp = client.post(
            f"/api/rewards/{r.id}/redeem",
            headers={"X-User-ID": "user-1"},
        )
        assert resp.status_code == 422

    def test_unique_redemption_codes(self, client_db):
        client, db = client_db
        r = _seed_reward(db, points_required=50, stock=None)
        _give_points(db, "user-1", 300)
        codes = set()
        for _ in range(3):
            resp = client.post(
                f"/api/rewards/{r.id}/redeem",
                headers={"X-User-ID": "user-1"},
            )
            assert resp.status_code == 201
            codes.add(resp.json()["redemption_code"])
        assert len(codes) == 3  # All codes must be unique

    def test_redemption_creates_ledger_entry(self, client_db):
        client, db = client_db
        r = _seed_reward(db, points_required=75)
        _give_points(db, "user-1", 200)
        client.post(f"/api/rewards/{r.id}/redeem", headers={"X-User-ID": "user-1"})
        db.expire_all()
        tx = (
            db.query(PointTransaction)
            .filter_by(user_id="user-1", transaction_type=TransactionType.REDEMPTION)
            .first()
        )
        assert tx is not None
        assert tx.amount == -75

    def test_no_negative_balance_after_redemption(self, client_db):
        client, db = client_db
        r = _seed_reward(db, points_required=100)
        _give_points(db, "user-1", 100)
        resp = client.post(
            f"/api/rewards/{r.id}/redeem",
            headers={"X-User-ID": "user-1"},
        )
        assert resp.status_code == 201
        db.expire_all()
        wallet = db.get(Wallet, "user-1")
        assert wallet.balance == 0
        # Second redemption should fail
        resp2 = client.post(
            f"/api/rewards/{r.id}/redeem",
            headers={"X-User-ID": "user-1"},
        )
        assert resp2.status_code == 422
        db.expire_all()
        wallet2 = db.get(Wallet, "user-1")
        assert wallet2.balance == 0  # Never negative


# ---------------------------------------------------------------------------
# Admin
# ---------------------------------------------------------------------------

class TestAdminRewards:
    def test_admin_create_reward(self, client_db):
        client, db = client_db
        payload = {
            "name": "Coffee Voucher",
            "description": "Free coffee",
            "provider": "CafeCo",
            "category": "food",
            "points_required": 50,
            "stock": 100,
        }
        resp = client.post(
            "/api/admin/rewards",
            json=payload,
            headers={"X-User-ID": "admin-1", "X-User-Role": "admin"},
        )
        assert resp.status_code == 201
        assert resp.json()["name"] == "Coffee Voucher"

    def test_non_admin_cannot_create_reward(self, client_db):
        client, db = client_db
        payload = {"name": "X", "points_required": 10}
        resp = client.post(
            "/api/admin/rewards",
            json=payload,
            headers={"X-User-ID": "user-1"},
        )
        assert resp.status_code == 403

    def test_admin_update_reward(self, client_db):
        client, db = client_db
        r = _seed_reward(db)
        resp = client.patch(
            f"/api/admin/rewards/{r.id}",
            json={"points_required": 200},
            headers={"X-User-ID": "admin-1", "X-User-Role": "admin"},
        )
        assert resp.status_code == 200
        assert resp.json()["points_required"] == 200

    def test_admin_deactivate_reward(self, client_db):
        client, db = client_db
        r = _seed_reward(db)
        resp = client.delete(
            f"/api/admin/rewards/{r.id}",
            headers={"X-User-ID": "admin-1", "X-User-Role": "admin"},
        )
        assert resp.status_code == 204
        db.expire_all()
        r_fresh = db.get(Reward, r.id)
        assert r_fresh.status == RewardStatus.INACTIVE

    def test_admin_analytics(self, client_db):
        client, db = client_db
        _seed_reward(db)
        resp = client.get(
            "/api/admin/reward-analytics",
            headers={"X-User-ID": "admin-1", "X-User-Role": "admin"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "total_redemptions" in data
        assert "active_rewards" in data

    def test_admin_point_adjust_positive(self, client_db):
        client, db = client_db
        resp = client.post(
            "/api/admin/users/user-1/points/adjust",
            json={"amount": 500, "reason": "Compensation"},
            headers={"X-User-ID": "admin-1", "X-User-Role": "admin"},
        )
        assert resp.status_code == 200
        assert resp.json()["new_balance"] == 500

    def test_admin_point_adjust_cannot_go_negative(self, client_db):
        client, db = client_db
        _give_points(db, "user-1", 100)
        resp = client.post(
            "/api/admin/users/user-1/points/adjust",
            json={"amount": -200, "reason": "Test"},
            headers={"X-User-ID": "admin-1", "X-User-Role": "admin"},
        )
        assert resp.status_code == 422

    def test_admin_list_all_redemptions(self, client_db):
        client, db = client_db
        r = _seed_reward(db, points_required=50)
        _give_points(db, "user-1", 200)
        client.post(f"/api/rewards/{r.id}/redeem", headers={"X-User-ID": "user-1"})
        resp = client.get(
            "/api/admin/redemptions",
            headers={"X-User-ID": "admin-1", "X-User-Role": "admin"},
        )
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1
