"""add finance default tables

Revision ID: 69e4324f2f5f
Revises: af4f6c2d1b90
Create Date: 2026-07-12 20:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "69e4324f2f5f"
down_revision: Union[str, Sequence[str], None] = "af4f6c2d1b90"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "financeleagueseason",
        sa.Column(
            "is_excluded",
            sa.Boolean(),
            nullable=True,
        ),
    )
    op.execute(
        "UPDATE financeleagueseason "
        "SET is_excluded = false "
        "WHERE is_excluded IS NULL"
    )
    op.alter_column(
        "financeleagueseason",
        "is_excluded",
        nullable=False,
        server_default=sa.false(),
    )

    op.create_table(
        "financeuserdefaults",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("site_user_id", sa.UUID(), nullable=False),
        sa.Column("buy_in_amount", sa.Float(), nullable=True),
        sa.Column("payout_structure", sa.JSON(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["site_user_id"], ["siteuser.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "site_user_id",
        ),
    )
    op.create_index(
        op.f("ix_financeuserdefaults_site_user_id"),
        "financeuserdefaults",
        ["site_user_id"],
        unique=True,
    )

    op.create_table(
        "financeleaguedefault",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("site_user_id", sa.UUID(), nullable=False),
        sa.Column("league_family_id", sa.String(), nullable=False),
        sa.Column("buy_in_amount", sa.Float(), nullable=True),
        sa.Column("payout_structure", sa.JSON(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["site_user_id"], ["siteuser.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "site_user_id",
            "league_family_id",
            name="uq_financeleaguedefault_site_user_family",
        ),
    )
    op.create_index(
        op.f("ix_financeleaguedefault_league_family_id"),
        "financeleaguedefault",
        ["league_family_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_financeleaguedefault_site_user_id"),
        "financeleaguedefault",
        ["site_user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_financeleaguedefault_site_user_id"),
        table_name="financeleaguedefault",
    )
    op.drop_index(
        op.f("ix_financeleaguedefault_league_family_id"),
        table_name="financeleaguedefault",
    )
    op.drop_table(
        "financeleaguedefault",
    )

    op.drop_index(
        op.f("ix_financeuserdefaults_site_user_id"),
        table_name="financeuserdefaults",
    )
    op.drop_table(
        "financeuserdefaults",
    )

    op.drop_column(
        "financeleagueseason",
        "is_excluded",
    )
