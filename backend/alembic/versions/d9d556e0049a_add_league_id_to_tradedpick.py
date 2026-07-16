"""add league_id to tradedpick

Revision ID: d9d556e0049a
Revises: 488ee922f3d6
Create Date: 2026-07-14 17:15:44.429129

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel



# revision identifiers, used by Alembic.
revision: str = 'd9d556e0049a'
down_revision: Union[str, Sequence[str], None] = '488ee922f3d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('tradedpick', sa.Column('league_id', sqlmodel.sql.sqltypes.AutoString(), nullable=True))

    op.execute("""
        UPDATE tradedpick tp
        SET league_id = t.league_id
        FROM "transaction" t
        WHERE tp.transaction_id = t.transaction_id
          AND tp.league_id IS NULL
    """)

    op.alter_column('tradedpick', 'league_id', nullable=False)
    op.create_index(op.f('ix_tradedpick_league_id'), 'tradedpick', ['league_id'], unique=False)
    op.create_foreign_key(None, 'tradedpick', 'league', ['league_id'], ['league_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(None, 'tradedpick', type_='foreignkey')
    op.drop_index(op.f('ix_tradedpick_league_id'), table_name='tradedpick')
    op.drop_column('tradedpick', 'league_id')
