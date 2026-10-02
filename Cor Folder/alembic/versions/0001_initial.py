"""initial production schema

Revision ID: 0001_initial
Revises:
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "crowd_observations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("place_id", sa.String(length=255), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("crowd_level", sa.String(length=30), nullable=False),
        sa.Column("source", sa.String(length=100), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.5"),
    )
    op.create_index("ix_crowd_observations_place_id", "crowd_observations", ["place_id"])
    op.create_index("ix_crowd_observations_timestamp", "crowd_observations", ["timestamp"])
    op.create_index("ix_crowd_observations_crowd_level", "crowd_observations", ["crowd_level"])
    op.create_index("ix_crowd_place_timestamp", "crowd_observations", ["place_id", "timestamp"])

    op.create_table(
        "place_season_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("place_id", sa.String(length=255), nullable=False),
        sa.Column("month", sa.Integer(), nullable=False),
        sa.Column("weather_score", sa.Float(), nullable=False),
        sa.Column("crowd_score", sa.Float(), nullable=False),
        sa.Column("festival_score", sa.Float(), nullable=False),
        sa.Column("accessibility_score", sa.Float(), nullable=False),
        sa.Column("overall_score", sa.Float(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False, server_default=""),
        sa.UniqueConstraint("place_id", "month", name="uq_place_month"),
    )
    op.create_index("ix_place_season_profiles_place_id", "place_season_profiles", ["place_id"])
    op.create_index("ix_place_season_profiles_month", "place_season_profiles", ["month"])
    op.create_index("ix_season_place_month", "place_season_profiles", ["place_id", "month"])


def downgrade():
    op.drop_table("place_season_profiles")
    op.drop_table("crowd_observations")
