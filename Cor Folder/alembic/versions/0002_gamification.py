"""
Alembic migration: Developer 2 gamification tables.

Revision ID: 0002_gamification
Revises: 0001_initial
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_gamification"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade():
    # visits
    op.create_table(
        "visits",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(255), nullable=False),
        sa.Column("place_id", sa.String(255), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column("verification_method", sa.String(30), nullable=True),
        sa.Column("verification_radius", sa.Float(), nullable=True),
        sa.Column("distance_from_place", sa.Float(), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("visit_reward_granted", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("photo_reward_granted", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_visits_user_id", "visits", ["user_id"])
    op.create_index("ix_visits_place_id", "visits", ["place_id"])
    op.create_index("ix_visits_status", "visits", ["status"])
    op.create_index("ix_visits_timestamp", "visits", ["timestamp"])
    op.create_index("ix_visits_user_place", "visits", ["user_id", "place_id"])
    op.create_index("ix_visits_user_status", "visits", ["user_id", "status"])

    # visit_proofs
    op.create_table(
        "visit_proofs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("visit_id", sa.Integer(), sa.ForeignKey("visits.id", ondelete="CASCADE"), nullable=False),
        sa.Column("image_url", sa.String(1024), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verification_status", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column("file_hash", sa.String(64), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_visit_proofs_visit_id", "visit_proofs", ["visit_id"])
    op.create_index("ix_visit_proofs_file_hash", "visit_proofs", ["file_hash"])

    # wallets
    op.create_table(
        "wallets",
        sa.Column("user_id", sa.String(255), primary_key=True),
        sa.Column("balance", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", name="uq_wallets_user_id"),
    )

    # point_transactions
    op.create_table(
        "point_transactions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(255), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("transaction_type", sa.String(30), nullable=False),
        sa.Column("reference_id", sa.String(255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_point_tx_user_id", "point_transactions", ["user_id"])
    op.create_index("ix_point_tx_created_at", "point_transactions", ["created_at"])
    op.create_index("ix_point_tx_type", "point_transactions", ["transaction_type"])

    # rewards
    op.create_table(
        "rewards",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("provider", sa.String(255), nullable=False, server_default=""),
        sa.Column("category", sa.String(100), nullable=False, server_default="general"),
        sa.Column("points_required", sa.Integer(), nullable=False),
        sa.Column("stock", sa.Integer(), nullable=True),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="ACTIVE"),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_rewards_status", "rewards", ["status"])
    op.create_index("ix_rewards_category", "rewards", ["category"])
    op.create_index("ix_rewards_provider", "rewards", ["provider"])

    # redemptions
    op.create_table(
        "redemptions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(255), nullable=False),
        sa.Column("reward_id", sa.Integer(), sa.ForeignKey("rewards.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("points_spent", sa.Integer(), nullable=False),
        sa.Column("redemption_code", sa.String(50), nullable=False, unique=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("redeemed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("redemption_code", name="uq_redemption_code"),
    )
    op.create_index("ix_redemptions_user_id", "redemptions", ["user_id"])
    op.create_index("ix_redemptions_reward_id", "redemptions", ["reward_id"])
    op.create_index("ix_redemptions_status", "redemptions", ["status"])


def downgrade():
    op.drop_table("redemptions")
    op.drop_table("rewards")
    op.drop_table("point_transactions")
    op.drop_table("wallets")
    op.drop_table("visit_proofs")
    op.drop_table("visits")
