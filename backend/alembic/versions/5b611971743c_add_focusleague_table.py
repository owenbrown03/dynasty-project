"""add focusleague table

Revision ID: 5b611971743c
Revises: 854a78cd165d
Create Date: 2026-08-24 03:30:26.338396

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel



# revision identifiers, used by Alembic.
revision: str = '5b611971743c'
down_revision: Union[str, Sequence[str], None] = '854a78cd165d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('focusleague',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('site_user_id', sa.UUID(), nullable=False),
    sa.Column('league_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['league_id'], ['league.league_id'], ),
    sa.ForeignKeyConstraint(['site_user_id'], ['siteuser.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('site_user_id', 'league_id', name='uq_focusleague_site_user_league')
    )
    op.create_index(op.f('ix_focusleague_league_id'), 'focusleague', ['league_id'], unique=False)
    op.create_index(op.f('ix_focusleague_site_user_id'), 'focusleague', ['site_user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_focusleague_site_user_id'), table_name='focusleague')
    op.drop_index(op.f('ix_focusleague_league_id'), table_name='focusleague')
    op.drop_table('focusleague')
