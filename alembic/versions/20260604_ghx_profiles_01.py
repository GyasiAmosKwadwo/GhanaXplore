"""Add tourist and operator profile tables.

This migration adds the one-to-one profile tables used by tourist and operator
accounts, while keeping operator ownership separate from attractions.
"""

from __future__ import annotations

import sys
from pathlib import Path

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from alembic import op

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.database import Base  # noqa: F401

# revision identifiers, used by Alembic.
revision = "20260604_ghx_profiles_01"
down_revision = "20260604_ghx_no2fa_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("tourist_profiles"):
        op.create_table(
            "tourist_profiles",
            sa.Column("id", PGUUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column(
                "user_id",
                PGUUID(as_uuid=True),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
                unique=True,
            ),
            sa.Column("preferred_language", sa.String(length=40), nullable=True),
            sa.Column("nationality", sa.String(length=80), nullable=True),
            sa.Column("home_region", sa.String(length=120), nullable=True),
            sa.Column("bio", sa.Text(), nullable=True),
            sa.Column("interests", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
            sa.Column(
                "travel_preferences",
                sa.JSON(),
                nullable=False,
                server_default=sa.text("'[]'::json"),
            ),
            sa.Column(
                "accessibility_needs",
                sa.JSON(),
                nullable=False,
                server_default=sa.text("'[]'::json"),
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
        )

    if not inspector.has_table("operator_profiles"):
        op.create_table(
            "operator_profiles",
            sa.Column("id", PGUUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column(
                "user_id",
                PGUUID(as_uuid=True),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
                unique=True,
            ),
            sa.Column("business_name", sa.String(length=255), nullable=True),
            sa.Column("business_description", sa.Text(), nullable=True),
            sa.Column("region", sa.String(length=120), nullable=True),
            sa.Column("district", sa.String(length=120), nullable=True),
            sa.Column("website", sa.String(length=255), nullable=True),
            sa.Column("license_number", sa.String(length=120), nullable=True),
            sa.Column("registration_number", sa.String(length=120), nullable=True),
            sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.text("false")),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("operator_profiles"):
        op.drop_table("operator_profiles")

    if inspector.has_table("tourist_profiles"):
        op.drop_table("tourist_profiles")
