"""merge league_type

Revision ID: d3f9e1a2b3c4
Revises: 20230820_add_league_type, 4c1d2e3f4a5b
Create Date: 2026-08-20 16:45:30.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "d3f9e1a2b3c4"
down_revision = ("20230820_add_league_type", "4c1d2e3f4a5b")
branch_labels = None
depends_on = None

def upgrade() -> None:
    """Merge-only revision: no DB operations required."""
    pass

def downgrade() -> None:
    """No-op downgrade for merge revision."""
    pass
