"""
Developer 2 — Tests for Wallet Service using an in-memory SQLite database.
"""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.gamification.models import (
    PointTransaction,
    TransactionType,
    Wallet,
    Visit,
    VisitProof,
    Reward,
    Redemption,
)
from app.gamification.wallet_service import WalletService


# ---------------------------------------------------------------------------
# Shared SQLite fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


# ---------------------------------------------------------------------------
# Wallet creation
# ---------------------------------------------------------------------------

class TestWalletCreation:
    def test_get_wallet_creates_if_missing(self, db):
        svc = WalletService()
        wallet = svc.get_wallet(db, "user-1")
        db.commit()
        assert wallet.user_id == "user-1"
        assert wallet.balance == 0

    def test_get_wallet_idempotent(self, db):
        svc = WalletService()
        w1 = svc.get_wallet(db, "user-1")
        db.commit()
        w2 = svc.get_wallet(db, "user-1")
        db.commit()
        assert w1.user_id == w2.user_id


# ---------------------------------------------------------------------------
# Earning points
# ---------------------------------------------------------------------------

class TestCredit:
    def test_credit_increases_balance(self, db):
        svc = WalletService()
        wallet, tx = svc.credit(db, "user-1", 50, TransactionType.VISIT_REWARD)
        db.commit()
        assert wallet.balance == 50
        assert tx.amount == 50
        assert tx.transaction_type == TransactionType.VISIT_REWARD

    def test_credit_creates_ledger_entry(self, db):
        svc = WalletService()
        svc.credit(db, "user-1", 50, TransactionType.VISIT_REWARD)
        db.commit()
        txs = db.query(PointTransaction).filter_by(user_id="user-1").all()
        assert len(txs) == 1
        assert txs[0].amount == 50

    def test_multiple_credits_accumulate(self, db):
        svc = WalletService()
        svc.credit(db, "user-1", 50, TransactionType.VISIT_REWARD)
        svc.credit(db, "user-1", 10, TransactionType.PHOTO_REWARD)
        db.commit()
        wallet = db.get(Wallet, "user-1")
        assert wallet.balance == 60
        count = db.query(PointTransaction).filter_by(user_id="user-1").count()
        assert count == 2

    def test_credit_zero_raises(self, db):
        svc = WalletService()
        with pytest.raises(ValueError):
            svc.credit(db, "user-1", 0, TransactionType.VISIT_REWARD)

    def test_credit_negative_raises(self, db):
        svc = WalletService()
        with pytest.raises(ValueError):
            svc.credit(db, "user-1", -10, TransactionType.VISIT_REWARD)


# ---------------------------------------------------------------------------
# Spending points
# ---------------------------------------------------------------------------

class TestDebit:
    def test_debit_decreases_balance(self, db):
        svc = WalletService()
        svc.credit(db, "user-1", 100, TransactionType.BONUS)
        db.commit()
        wallet, tx = svc.debit(db, "user-1", 40, TransactionType.REDEMPTION)
        db.commit()
        assert wallet.balance == 60
        assert tx.amount == -40

    def test_insufficient_points_raises_422(self, db):
        from fastapi import HTTPException
        svc = WalletService()
        svc.credit(db, "user-1", 30, TransactionType.BONUS)
        db.commit()
        with pytest.raises(HTTPException) as exc_info:
            svc.debit(db, "user-1", 50, TransactionType.REDEMPTION)
        assert exc_info.value.status_code == 422
        assert exc_info.value.detail["code"] == "INSUFFICIENT_POINTS"

    def test_balance_never_negative(self, db):
        from fastapi import HTTPException
        svc = WalletService()
        svc.credit(db, "user-1", 100, TransactionType.BONUS)
        db.commit()
        with pytest.raises(HTTPException):
            svc.debit(db, "user-1", 101, TransactionType.REDEMPTION)
        db.rollback()
        wallet = db.get(Wallet, "user-1")
        assert wallet.balance == 100


# ---------------------------------------------------------------------------
# Admin adjustment
# ---------------------------------------------------------------------------

class TestAdminAdjust:
    def test_positive_adjustment(self, db):
        svc = WalletService()
        wallet, tx = svc.admin_adjust(db, "user-1", 100, "Correction", "admin-1")
        db.commit()
        assert wallet.balance == 100
        assert tx.transaction_type == TransactionType.ADMIN_ADJUSTMENT

    def test_negative_adjustment(self, db):
        svc = WalletService()
        svc.credit(db, "user-1", 200, TransactionType.BONUS)
        db.commit()
        wallet, tx = svc.admin_adjust(db, "user-1", -50, "Adjustment", "admin-1")
        db.commit()
        assert wallet.balance == 150

    def test_negative_adjustment_cannot_go_below_zero(self, db):
        from fastapi import HTTPException
        svc = WalletService()
        svc.credit(db, "user-1", 50, TransactionType.BONUS)
        db.commit()
        with pytest.raises(HTTPException) as exc_info:
            svc.admin_adjust(db, "user-1", -100, "Test", "admin-1")
        assert exc_info.value.status_code == 422


# ---------------------------------------------------------------------------
# Transaction history
# ---------------------------------------------------------------------------

class TestTransactionHistory:
    def test_transactions_returned_in_desc_order(self, db):
        svc = WalletService()
        svc.credit(db, "user-1", 50, TransactionType.VISIT_REWARD)
        svc.credit(db, "user-1", 10, TransactionType.PHOTO_REWARD)
        db.commit()
        items, total = svc.get_transactions(db, "user-1", page=1, page_size=10)
        assert total == 2
        # Most recent first
        assert items[0].amount == 10
        assert items[1].amount == 50

    def test_pagination(self, db):
        svc = WalletService()
        for i in range(5):
            svc.credit(db, "user-1", 10, TransactionType.BONUS)
        db.commit()
        page1, total = svc.get_transactions(db, "user-1", page=1, page_size=3)
        page2, _ = svc.get_transactions(db, "user-1", page=2, page_size=3)
        assert total == 5
        assert len(page1) == 3
        assert len(page2) == 2

    def test_only_own_transactions_returned(self, db):
        svc = WalletService()
        svc.credit(db, "user-1", 50, TransactionType.BONUS)
        svc.credit(db, "user-2", 100, TransactionType.BONUS)
        db.commit()
        items, total = svc.get_transactions(db, "user-1")
        assert total == 1
        assert items[0].user_id == "user-1"
