"""add hidden leagues table

Revision ID: a4a7c2e4b1ce
Revises: 54a0e3d50f1c
Create Date: 2026-07-12 15:35:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "a4a7c2e4b1ce"
down_revision: Union[str, None] = "54a0e3d50f1c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "hiddenleague",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "site_user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("league_id", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["league_id"],
            ["league.league_id"],
        ),
        sa.ForeignKeyConstraint(
            ["site_user_id"],
            ["siteuser.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "site_user_id",
            "league_id",
            name="uq_hiddenleague_site_user_league",
        ),
    )
    op.create_index(
        op.f("ix_hiddenleague_league_id"),
        "hiddenleague",
        ["league_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_hiddenleague_site_user_id"),
        "hiddenleague",
        ["site_user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_hiddenleague_site_user_id"),
        table_name="hiddenleague",
    )
    op.drop_index(
        op.f("ix_hiddenleague_league_id"),
        table_name="hiddenleague",
    )
    op.drop_table("hiddenleague")
