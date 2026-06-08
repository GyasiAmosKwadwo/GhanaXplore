"""merge booking slot and attraction activity heads

Revision ID: 992c9860de48
Revises: ghx_booking_slot_01, 20260608_ghx_attraction_activity_01
Create Date: 2026-06-08 20:20:44.658118

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '992c9860de48'
down_revision = ('ghx_booking_slot_01', '20260608_ghx_attraction_activity_01')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
