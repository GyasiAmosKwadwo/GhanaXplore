"""Add time_slot_id to bookings for capacity-aware scheduling."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID as PGUUID

# revision identifiers, used by Alembic.
revision = "ghx_booking_slot_01"
down_revision = "20260604_ghx_profiles_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("bookings")}

    if "time_slot_id" not in columns:
        op.add_column(
            "bookings",
            sa.Column("time_slot_id", PGUUID(as_uuid=True), nullable=True),
        )
        op.create_foreign_key(
            "fk_bookings_time_slot_id",
            "bookings",
            "time_slots",
            ["time_slot_id"],
            ["id"],
            ondelete="SET NULL",
        )
        op.create_index("ix_bookings_time_slot_id", "bookings", ["time_slot_id"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("bookings")}

    if "time_slot_id" in columns:
        op.drop_index("ix_bookings_time_slot_id", table_name="bookings")
        op.drop_constraint("fk_bookings_time_slot_id", "bookings", type_="foreignkey")
        op.drop_column("bookings", "time_slot_id")
