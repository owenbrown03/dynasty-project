"""add adp snapshot tables

Revision ID: 4c1d2e3f4a5b
Revises: 9b2d3f4a5c6d
Create Date: 2026-07-18 01:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "4c1d2e3f4a5b"
down_revision: Union[str, Sequence[str], None] = "9b2d3f4a5c6d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "adpsnapshot",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("calculation_version", sa.String(), nullable=False),
        sa.Column("season", sa.String(), nullable=True),
        sa.Column("draft_kind", sa.String(), nullable=True),
        sa.Column("qb_format", sa.String(), nullable=True),
        sa.Column("te_premium", sa.String(), nullable=True),
        sa.Column("team_count", sa.Integer(), nullable=True),
        sa.Column("scoring_format", sa.String(), nullable=True),
        sa.Column("start_date", sa.DateTime(), nullable=True),
        sa.Column("end_date", sa.DateTime(), nullable=True),
        sa.Column("minimum_draft_count", sa.Integer(), nullable=False),
        sa.Column("draft_count", sa.Integer(), nullable=False),
        sa.Column("pick_count", sa.Integer(), nullable=False),
        sa.Column("earliest_draft_at", sa.DateTime(), nullable=True),
        sa.Column("latest_draft_at", sa.DateTime(), nullable=True),
        sa.Column("generated_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_adpsnapshot_calculation_version"),
        "adpsnapshot",
        ["calculation_version"],
        unique=False,
    )
    op.create_index(
        op.f("ix_adpsnapshot_season"),
        "adpsnapshot",
        ["season"],
        unique=False,
    )
    op.create_index(
        op.f("ix_adpsnapshot_draft_kind"),
        "adpsnapshot",
        ["draft_kind"],
        unique=False,
    )
    op.create_index(
        op.f("ix_adpsnapshot_qb_format"),
        "adpsnapshot",
        ["qb_format"],
        unique=False,
    )
    op.create_index(
        op.f("ix_adpsnapshot_te_premium"),
        "adpsnapshot",
        ["te_premium"],
        unique=False,
    )
    op.create_index(
        op.f("ix_adpsnapshot_team_count"),
        "adpsnapshot",
        ["team_count"],
        unique=False,
    )
    op.create_index(
        op.f("ix_adpsnapshot_scoring_format"),
        "adpsnapshot",
        ["scoring_format"],
        unique=False,
    )
    op.create_index(
        op.f("ix_adpsnapshot_start_date"),
        "adpsnapshot",
        ["start_date"],
        unique=False,
    )
    op.create_index(
        op.f("ix_adpsnapshot_end_date"),
        "adpsnapshot",
        ["end_date"],
        unique=False,
    )
    op.create_index(
        op.f("ix_adpsnapshot_minimum_draft_count"),
        "adpsnapshot",
        ["minimum_draft_count"],
        unique=False,
    )
    op.create_index(
        op.f("ix_adpsnapshot_generated_at"),
        "adpsnapshot",
        ["generated_at"],
        unique=False,
    )

    op.create_table(
        "adpsnapshotplayer",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("snapshot_id", sa.String(), nullable=False),
        sa.Column("player_id", sa.String(), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("position", sa.String(), nullable=True),
        sa.Column("team", sa.String(), nullable=True),
        sa.Column("overall_adp", sa.Float(), nullable=False),
        sa.Column("median_pick", sa.Float(), nullable=False),
        sa.Column("min_pick", sa.Integer(), nullable=False),
        sa.Column("max_pick", sa.Integer(), nullable=False),
        sa.Column("standard_deviation", sa.Float(), nullable=True),
        sa.Column("pick_count", sa.Integer(), nullable=False),
        sa.Column("draft_count", sa.Integer(), nullable=False),
        sa.Column("selection_rate", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["snapshot_id"], ["adpsnapshot.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_adpsnapshotplayer_snapshot_id"),
        "adpsnapshotplayer",
        ["snapshot_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_adpsnapshotplayer_player_id"),
        "adpsnapshotplayer",
        ["player_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_adpsnapshotplayer_rank"),
        "adpsnapshotplayer",
        ["rank"],
        unique=False,
    )
    op.create_index(
        "ix_adpsnapshotplayer_snapshot_rank",
        "adpsnapshotplayer",
        ["snapshot_id", "rank"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_adpsnapshotplayer_snapshot_rank",
        table_name="adpsnapshotplayer",
    )
    op.drop_index(
        op.f("ix_adpsnapshotplayer_rank"),
        table_name="adpsnapshotplayer",
    )
    op.drop_index(
        op.f("ix_adpsnapshotplayer_player_id"),
        table_name="adpsnapshotplayer",
    )
    op.drop_index(
        op.f("ix_adpsnapshotplayer_snapshot_id"),
        table_name="adpsnapshotplayer",
    )
    op.drop_table("adpsnapshotplayer")

    op.drop_index(
        op.f("ix_adpsnapshot_generated_at"),
        table_name="adpsnapshot",
    )
    op.drop_index(
        op.f("ix_adpsnapshot_minimum_draft_count"),
        table_name="adpsnapshot",
    )
    op.drop_index(
        op.f("ix_adpsnapshot_end_date"),
        table_name="adpsnapshot",
    )
    op.drop_index(
        op.f("ix_adpsnapshot_start_date"),
        table_name="adpsnapshot",
    )
    op.drop_index(
        op.f("ix_adpsnapshot_scoring_format"),
        table_name="adpsnapshot",
    )
    op.drop_index(
        op.f("ix_adpsnapshot_team_count"),
        table_name="adpsnapshot",
    )
    op.drop_index(
        op.f("ix_adpsnapshot_te_premium"),
        table_name="adpsnapshot",
    )
    op.drop_index(
        op.f("ix_adpsnapshot_qb_format"),
        table_name="adpsnapshot",
    )
    op.drop_index(
        op.f("ix_adpsnapshot_draft_kind"),
        table_name="adpsnapshot",
    )
    op.drop_index(
        op.f("ix_adpsnapshot_season"),
        table_name="adpsnapshot",
    )
    op.drop_index(
        op.f("ix_adpsnapshot_calculation_version"),
        table_name="adpsnapshot",
    )
    op.drop_table("adpsnapshot")
