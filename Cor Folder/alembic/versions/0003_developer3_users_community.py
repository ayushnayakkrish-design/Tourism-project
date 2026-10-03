"""Developer 3 identity, community, localization, and moderation tables.

Revision ID: 0003_developer3
Revises: 0002_gamification
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_developer3"
down_revision = "0002_gamification"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("email", sa.String(254), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(80), nullable=False),
        sa.Column("bio", sa.Text(), nullable=False, server_default=""),
        sa.Column("role", sa.String(32), nullable=False, server_default="TOURIST"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_role", "users", ["role"])

    op.create_table(
        "user_preferences",
        sa.Column("user_id", sa.String(64), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("language", sa.String(10), nullable=False, server_default="en"),
        sa.Column("theme", sa.String(12), nullable=False, server_default="system"),
        sa.Column("voice_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("units", sa.String(12), nullable=False, server_default="metric"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "community_submissions",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.String(64), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.String(40), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("photos", sa.JSON(), nullable=False),
        sa.Column("language", sa.String(10), nullable=False, server_default="en"),
        sa.Column("status", sa.String(16), nullable=False, server_default="PENDING"),
        sa.Column("moderator_id", sa.String(64), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("moderator_note", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_community_submissions_user_id", "community_submissions", ["user_id"])
    op.create_index("ix_community_submissions_type", "community_submissions", ["type"])
    op.create_index("ix_community_submissions_status", "community_submissions", ["status"])
    op.create_index("ix_community_status_created", "community_submissions", ["status", "created_at"])

    op.create_table(
        "reviews",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.String(64), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("place_id", sa.String(255), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", sa.String(16), nullable=False, server_default="PENDING"),
        sa.Column("moderator_id", sa.String(64), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("moderator_note", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", "place_id", name="uq_review_user_place"),
    )
    op.create_index("ix_reviews_user_id", "reviews", ["user_id"])
    op.create_index("ix_reviews_status", "reviews", ["status"])
    op.create_index("ix_reviews_place_status", "reviews", ["place_id", "status"])

    op.create_table(
        "place_content",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("place_id", sa.String(255), nullable=False),
        sa.Column("language", sa.String(10), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("rules", sa.Text(), nullable=False, server_default=""),
        sa.Column("tips", sa.Text(), nullable=False, server_default=""),
        sa.Column("source", sa.String(32), nullable=False, server_default="community"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("place_id", "language", name="uq_place_content_language"),
    )
    op.create_index("ix_place_content_place_id", "place_content", ["place_id"])

    op.create_table(
        "translation_cache",
        sa.Column("cache_key", sa.String(64), primary_key=True),
        sa.Column("translation", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "moderation_actions",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("moderator_id", sa.String(64), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("target_type", sa.String(24), nullable=False),
        sa.Column("target_id", sa.String(64), nullable=False),
        sa.Column("action", sa.String(24), nullable=False),
        sa.Column("note", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_moderation_target", "moderation_actions", ["target_type", "target_id"])


def downgrade():
    op.drop_table("moderation_actions")
    op.drop_table("translation_cache")
    op.drop_table("place_content")
    op.drop_table("reviews")
    op.drop_table("community_submissions")
    op.drop_table("user_preferences")
    op.drop_table("users")
