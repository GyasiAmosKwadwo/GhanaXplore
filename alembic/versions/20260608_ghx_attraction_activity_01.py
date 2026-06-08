"""Add attraction activity table.

Revision ID: 20260608_ghx_attraction_activity_01
Revises: 20260604_ghx_core_0001
Create Date: 2026-06-08 00:00:00.000000
"""

import sys
from pathlib import Path

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# revision identifiers, used by Alembic.
revision = "20260608_ghx_attraction_activity_01"
down_revision = "20260604_ghx_core_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "attraction_activities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("attraction_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("price_ghs", sa.Numeric(12, 2), nullable=True),
        sa.Column("price_usd", sa.Numeric(12, 2), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("max_participants", sa.Integer(), nullable=True),
        sa.Column("includes", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("excludes", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("restrictions", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("images", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("is_available", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("requires_advance_booking", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["attraction_id"], ["attractions.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_attraction_activities_attraction_id",
        "attraction_activities",
        ["attraction_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_attraction_activities_attraction_id", table_name="attraction_activities")
    op.drop_table("attraction_activities")
