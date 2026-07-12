"""add player season stats table

Revision ID: 8c1af9c43b81
Revises: dc4aa2a4ef02
Create Date: 2026-07-12 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8c1af9c43b81"
down_revision: Union[str, Sequence[str], None] = "dc4aa2a4ef02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "playerseasonstats",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("player_id", sa.String(), nullable=False),
        sa.Column("season", sa.Integer(), nullable=False),
        sa.Column("season_type", sa.String(), nullable=False),
        sa.Column("source", sa.String(), nullable=False),
        sa.Column("games_played", sa.Float(), nullable=False),
        sa.Column("pass_att", sa.Float(), nullable=False),
        sa.Column("pass_cmp", sa.Float(), nullable=False),
        sa.Column("pass_yd", sa.Float(), nullable=False),
        sa.Column("pass_td", sa.Float(), nullable=False),
        sa.Column("pass_int", sa.Float(), nullable=False),
        sa.Column("pass_2pt", sa.Float(), nullable=False),
        sa.Column("rush_att", sa.Float(), nullable=False),
        sa.Column("rush_yd", sa.Float(), nullable=False),
        sa.Column("rush_td", sa.Float(), nullable=False),
        sa.Column("rush_2pt", sa.Float(), nullable=False),
        sa.Column("rec", sa.Float(), nullable=False),
        sa.Column("rec_yd", sa.Float(), nullable=False),
        sa.Column("rec_td", sa.Float(), nullable=False),
        sa.Column("rec_2pt", sa.Float(), nullable=False),
        sa.Column("fum_lost", sa.Float(), nullable=False),
        sa.Column("pass_fd", sa.Float(), nullable=False),
        sa.Column("rush_fd", sa.Float(), nullable=False),
        sa.Column("rec_fd", sa.Float(), nullable=False),
        sa.Column("rec_0_4", sa.Float(), nullable=False),
        sa.Column("rec_5_9", sa.Float(), nullable=False),
        sa.Column("rec_10_19", sa.Float(), nullable=False),
        sa.Column("rec_20_29", sa.Float(), nullable=False),
        sa.Column("rec_30_39", sa.Float(), nullable=False),
        sa.Column("rec_40p", sa.Float(), nullable=False),
        sa.Column("bonus_rec_rb", sa.Float(), nullable=False),
        sa.Column("bonus_rec_wr", sa.Float(), nullable=False),
        sa.Column("bonus_rec_te", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["player_id"], ["player.player_id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_playerseasonstats_player_id"), "playerseasonstats", ["player_id"], unique=False)
    op.create_index(op.f("ix_playerseasonstats_season"), "playerseasonstats", ["season"], unique=False)
    op.create_index(op.f("ix_playerseasonstats_season_type"), "playerseasonstats", ["season_type"], unique=False)
    op.create_index(op.f("ix_playerseasonstats_source"), "playerseasonstats", ["source"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_playerseasonstats_source"), table_name="playerseasonstats")
    op.drop_index(op.f("ix_playerseasonstats_season_type"), table_name="playerseasonstats")
    op.drop_index(op.f("ix_playerseasonstats_season"), table_name="playerseasonstats")
    op.drop_index(op.f("ix_playerseasonstats_player_id"), table_name="playerseasonstats")
    op.drop_table("playerseasonstats")
