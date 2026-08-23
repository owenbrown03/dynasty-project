"""add advisor report table

Revision ID: 854a78cd165d
Revises: c13c06e92458
Create Date: 2026-08-22 19:40:06.766529

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel



# revision identifiers, used by Alembic.
revision: str = '854a78cd165d'
down_revision: Union[str, Sequence[str], None] = 'c13c06e92458'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('advisorreport',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('site_user_id', sa.UUID(), nullable=False),
    sa.Column('username', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('payload', sa.JSON(), nullable=False),
    sa.Column('model', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('generated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['site_user_id'], ['siteuser.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_advisorreport_site_user_id'), 'advisorreport', ['site_user_id'], unique=False)
    op.create_index(op.f('ix_advisorreport_username'), 'advisorreport', ['username'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_advisorreport_username'), table_name='advisorreport')
    op.drop_index(op.f('ix_advisorreport_site_user_id'), table_name='advisorreport')
    op.drop_table('advisorreport')
