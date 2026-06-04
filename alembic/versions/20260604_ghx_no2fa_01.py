"""Remove legacy 2FA columns from users.

This migration is safe to run on databases that already had the legacy
two-factor columns as well as fresh databases where those columns never
existed.
"""

import sys
from pathlib import Path

import sqlalchemy as sa
from alembic import op

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.database import Base  # noqa: F401

# revision identifiers, used by Alembic.
revision = "20260604_ghx_no2fa_01"
down_revision = "20260604_ghx_core_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("users"):
        return

    columns = {column["name"] for column in inspector.get_columns("users")}
    for column_name in ("two_factor_secret", "two_factor_method", "two_factor_enabled"):
        if column_name in columns:
            op.drop_column("users", column_name)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("users"):
        return

    columns = {column["name"] for column in inspector.get_columns("users")}

    if "two_factor_enabled" not in columns:
        op.add_column(
            "users",
            sa.Column(
                "two_factor_enabled",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false"),
            ),
        )

    if "two_factor_secret" not in columns:
        op.add_column("users", sa.Column("two_factor_secret", sa.String(length=32), nullable=True))

    if "two_factor_method" not in columns:
        op.add_column("users", sa.Column("two_factor_method", sa.String(length=20), nullable=True))
