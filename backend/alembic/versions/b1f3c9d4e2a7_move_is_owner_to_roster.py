"""move is_owner from user -> roster

Revision ID: b1f3c9d4e2a7
Revises: 771b6bb3cb32
Create Date: 2026-07-13 18:54:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b1f3c9d4e2a7'
down_revision: Union[str, Sequence[str], None] = '771b6bb3cb32'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: add roster.is_owner, backfill where unambiguous, drop user.is_owner."""
    # Add is_owner to roster
    op.add_column('roster', sa.Column('is_owner', sa.Boolean(), nullable=True))

    # Backfill: if a user had is_owner=True and that user only owns a single roster,
    # copy that flag to the roster row. This preserves unambiguous ownership markers.
    op.execute("""
    UPDATE roster
    SET is_owner = true
    FROM "user"
    WHERE roster.owner_id = "user".user_id
      AND "user".is_owner = true
      AND (
        SELECT COUNT(*) FROM roster r2 WHERE r2.owner_id = "user".user_id
      ) = 1
    """)

    # Drop is_owner from user table
    with op.batch_alter_table('user') as batch_op:
        batch_op.drop_column('is_owner')


def downgrade() -> None:
    """Downgrade schema: re-add user.is_owner, backfill from roster where unambiguous, drop roster.is_owner."""
    # Re-add user.is_owner
    op.add_column('user', sa.Column('is_owner', sa.Boolean(), nullable=True))

    # Backfill user.is_owner for owners who are unambiguously commissionners (one roster)
    # Use an aggregated subquery to only restore when exactly one roster exists for the user.
    op.execute("""
    UPDATE "user"
    SET is_owner = sub.is_owner
    FROM (
      SELECT owner_id, bool_or(is_owner) AS is_owner, COUNT(*) AS cnt
      FROM roster
      WHERE owner_id IS NOT NULL
      GROUP BY owner_id
    ) AS sub
    WHERE "user".user_id = sub.owner_id
      AND sub.cnt = 1
      AND sub.is_owner = true
    """)

    # Drop roster.is_owner
    with op.batch_alter_table('roster') as batch_op:
        batch_op.drop_column('is_owner')
