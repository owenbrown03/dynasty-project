"""add playoff matchups table

Revision ID: 54a0e3d50f1c
Revises: 69e4324f2f5f
Create Date: 2026-07-12 21:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "54a0e3d50f1c"
down_revision: Union[str, Sequence[str], None] = "69e4324f2f5f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "playoffmatchup",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("league_id", sa.String(), nullable=False),
        sa.Column("bracket_type", sa.String(), nullable=False),
        sa.Column("round", sa.Integer(), nullable=False),
        sa.Column("matchup_id", sa.Integer(), nullable=False),
        sa.Column("team_one_roster_id", sa.Integer(), nullable=True),
        sa.Column("team_two_roster_id", sa.Integer(), nullable=True),
        sa.Column("team_one_from_winner_matchup_id", sa.Integer(), nullable=True),
        sa.Column("team_one_from_loser_matchup_id", sa.Integer(), nullable=True),
        sa.Column("team_two_from_winner_matchup_id", sa.Integer(), nullable=True),
        sa.Column("team_two_from_loser_matchup_id", sa.Integer(), nullable=True),
        sa.Column("winner_roster_id", sa.Integer(), nullable=True),
        sa.Column("loser_roster_id", sa.Integer(), nullable=True),
        sa.Column("placement", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["league_id"], ["league.league_id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "league_id",
            "bracket_type",
            "round",
            "matchup_id",
            name="uq_playoffmatchup_league_bracket_round_matchup",
        ),
    )
    op.create_index(
        op.f("ix_playoffmatchup_league_id"),
        "playoffmatchup",
        ["league_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_playoffmatchup_bracket_type"),
        "playoffmatchup",
        ["bracket_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_playoffmatchup_round"),
        "playoffmatchup",
        ["round"],
        unique=False,
    )
    op.create_index(
        op.f("ix_playoffmatchup_matchup_id"),
        "playoffmatchup",
        ["matchup_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_playoffmatchup_winner_roster_id"),
        "playoffmatchup",
        ["winner_roster_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_playoffmatchup_loser_roster_id"),
        "playoffmatchup",
        ["loser_roster_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_playoffmatchup_placement"),
        "playoffmatchup",
        ["placement"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_playoffmatchup_placement"),
        table_name="playoffmatchup",
    )
    op.drop_index(
        op.f("ix_playoffmatchup_loser_roster_id"),
        table_name="playoffmatchup",
    )
    op.drop_index(
        op.f("ix_playoffmatchup_winner_roster_id"),
        table_name="playoffmatchup",
    )
    op.drop_index(
        op.f("ix_playoffmatchup_matchup_id"),
        table_name="playoffmatchup",
    )
    op.drop_index(
        op.f("ix_playoffmatchup_round"),
        table_name="playoffmatchup",
    )
    op.drop_index(
        op.f("ix_playoffmatchup_bracket_type"),
        table_name="playoffmatchup",
    )
    op.drop_index(
        op.f("ix_playoffmatchup_league_id"),
        table_name="playoffmatchup",
    )
    op.drop_table("playoffmatchup")
