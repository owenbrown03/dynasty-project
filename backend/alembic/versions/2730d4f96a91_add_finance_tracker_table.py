"""add finance tracker table

Revision ID: 2730d4f96a91
Revises: 7c2f4b7b1f8d
Create Date: 2026-07-12 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2730d4f96a91"
down_revision: Union[str, Sequence[str], None] = "7c2f4b7b1f8d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "financeleagueseason",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("site_user_id", sa.UUID(), nullable=False),
        sa.Column("league_id", sa.String(), nullable=False),
        sa.Column("season", sa.String(), nullable=False),
        sa.Column("buy_in_amount", sa.Float(), nullable=False),
        sa.Column("winnings_amount", sa.Float(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["league_id"], ["league.league_id"]),
        sa.ForeignKeyConstraint(["site_user_id"], ["siteuser.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "site_user_id",
            "league_id",
            "season",
            name="uq_financeleagueseason_site_user_league_season",
        ),
    )
    op.create_index(
        op.f("ix_financeleagueseason_league_id"),
        "financeleagueseason",
        ["league_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_financeleagueseason_season"),
        "financeleagueseason",
        ["season"],
        unique=False,
    )
    op.create_index(
        op.f("ix_financeleagueseason_site_user_id"),
        "financeleagueseason",
        ["site_user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_financeleagueseason_site_user_id"),
        table_name="financeleagueseason",
    )
    op.drop_index(
        op.f("ix_financeleagueseason_season"),
        table_name="financeleagueseason",
    )
    op.drop_index(
        op.f("ix_financeleagueseason_league_id"),
        table_name="financeleagueseason",
    )
    op.drop_table("financeleagueseason")
