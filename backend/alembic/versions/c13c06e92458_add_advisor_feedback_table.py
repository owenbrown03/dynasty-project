"""add advisor feedback table

Revision ID: c13c06e92458
Revises: d3f9e1a2b3c4
Create Date: 2026-08-22 19:24:55.596355

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel



# revision identifiers, used by Alembic.
revision: str = 'c13c06e92458'
down_revision: Union[str, Sequence[str], None] = 'd3f9e1a2b3c4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('advisorfeedback',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('site_user_id', sa.UUID(), nullable=False),
    sa.Column('league_id', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('counterparty_id', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('player_ids', sa.JSON(), nullable=False),
    sa.Column('sentiment', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('reason', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('tags', sa.JSON(), nullable=False),
    sa.Column('proposal_snapshot', sa.JSON(), nullable=False),
    sa.Column('action_taken', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('resolved', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['league_id'], ['league.league_id'], ),
    sa.ForeignKeyConstraint(['site_user_id'], ['siteuser.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_advisorfeedback_league_id'), 'advisorfeedback', ['league_id'], unique=False)
    op.create_index(op.f('ix_advisorfeedback_sentiment'), 'advisorfeedback', ['sentiment'], unique=False)
    op.create_index(op.f('ix_advisorfeedback_site_user_id'), 'advisorfeedback', ['site_user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_advisorfeedback_site_user_id'), table_name='advisorfeedback')
    op.drop_index(op.f('ix_advisorfeedback_sentiment'), table_name='advisorfeedback')
    op.drop_index(op.f('ix_advisorfeedback_league_id'), table_name='advisorfeedback')
    op.drop_table('advisorfeedback')
