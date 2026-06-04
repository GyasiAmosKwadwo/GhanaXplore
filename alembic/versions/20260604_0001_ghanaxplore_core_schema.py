"""Create the GhanaXplore core schema.

This baseline migration creates the current SQLAlchemy metadata so the app can
move away from startup table auto-creation and rely on Alembic instead.
"""

import sys
from pathlib import Path

from alembic import op

# Ensure the repository root is importable when Alembic loads this file directly.
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.database import Base

# revision identifiers, used by Alembic.
revision = "20260604_ghx_core_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
