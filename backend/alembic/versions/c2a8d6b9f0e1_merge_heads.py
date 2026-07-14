"""merge heads

Revision ID: c2a8d6b9f0e1
Revises: 4ed89f8389c6, b1f3c9d4e2a7
Create Date: 2026-07-13 19:05:00.000000

This is an Alembic merge revision to resolve multiple heads.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c2a8d6b9f0e1'
down_revision: Union[str, Sequence[str], None] = (
    '4ed89f8389c6',
    'b1f3c9d4e2a7',
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Merge-only revision: no DB operations required."""
    pass


def downgrade() -> None:
    """No-op downgrade for merge revision."""
    pass
