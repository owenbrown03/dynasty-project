"""add commissioner workspace tables

Revision ID: 7c2f4b7b1f8d
Revises: 0a2d1f8f6d91
Create Date: 2026-07-12 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7c2f4b7b1f8d"
down_revision: Union[str, Sequence[str], None] = "0a2d1f8f6d91"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "commissionerleaguenote",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("site_user_id", sa.UUID(), nullable=False),
        sa.Column("league_id", sa.String(), nullable=False),
        sa.Column("note", sa.String(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["league_id"], ["league.league_id"]),
        sa.ForeignKeyConstraint(["site_user_id"], ["siteuser.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "site_user_id",
            "league_id",
            name="uq_commissionerleaguenote_site_user_league",
        ),
    )
    op.create_index(
        op.f("ix_commissionerleaguenote_league_id"),
        "commissionerleaguenote",
        ["league_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_commissionerleaguenote_site_user_id"),
        "commissionerleaguenote",
        ["site_user_id"],
        unique=False,
    )

    op.create_table(
        "commissionerleaguedues",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("site_user_id", sa.UUID(), nullable=False),
        sa.Column("league_id", sa.String(), nullable=False),
        sa.Column("roster_id", sa.Integer(), nullable=False),
        sa.Column("season", sa.String(), nullable=False),
        sa.Column("buy_in_amount", sa.Float(), nullable=True),
        sa.Column("is_paid", sa.Boolean(), nullable=False),
        sa.Column("paid_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["league_id"], ["league.league_id"]),
        sa.ForeignKeyConstraint(["site_user_id"], ["siteuser.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "site_user_id",
            "league_id",
            "roster_id",
            "season",
            name="uq_commissionerleaguedues_site_user_league_roster_season",
        ),
    )
    op.create_index(
        op.f("ix_commissionerleaguedues_league_id"),
        "commissionerleaguedues",
        ["league_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_commissionerleaguedues_roster_id"),
        "commissionerleaguedues",
        ["roster_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_commissionerleaguedues_season"),
        "commissionerleaguedues",
        ["season"],
        unique=False,
    )
    op.create_index(
        op.f("ix_commissionerleaguedues_site_user_id"),
        "commissionerleaguedues",
        ["site_user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_commissionerleaguedues_site_user_id"),
        table_name="commissionerleaguedues",
    )
    op.drop_index(
        op.f("ix_commissionerleaguedues_season"),
        table_name="commissionerleaguedues",
    )
    op.drop_index(
        op.f("ix_commissionerleaguedues_roster_id"),
        table_name="commissionerleaguedues",
    )
    op.drop_index(
        op.f("ix_commissionerleaguedues_league_id"),
        table_name="commissionerleaguedues",
    )
    op.drop_table("commissionerleaguedues")

    op.drop_index(
        op.f("ix_commissionerleaguenote_site_user_id"),
        table_name="commissionerleaguenote",
    )
    op.drop_index(
        op.f("ix_commissionerleaguenote_league_id"),
        table_name="commissionerleaguenote",
    )
    op.drop_table("commissionerleaguenote")
