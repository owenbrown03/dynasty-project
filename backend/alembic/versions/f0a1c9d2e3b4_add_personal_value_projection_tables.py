"""add personal value projection tables

Revision ID: f0a1c9d2e3b4
Revises: a4a7c2e4b1ce
Create Date: 2026-07-12 21:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f0a1c9d2e3b4"
down_revision: Union[str, Sequence[str], None] = "a4a7c2e4b1ce"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "personalprojection",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("site_user_id", sa.UUID(), nullable=False),
        sa.Column("player_id", sa.String(), nullable=False),
        sa.Column("season", sa.Integer(), nullable=False),
        sa.Column("position", sa.String(), nullable=False),
        sa.Column("default_source", sa.String(), nullable=False),
        sa.Column("is_customized", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["player_id"], ["player.player_id"]),
        sa.ForeignKeyConstraint(["site_user_id"], ["siteuser.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "site_user_id",
            "player_id",
            "season",
            name="uq_personalprojection_site_user_player_season",
        ),
    )
    op.create_index(
        op.f("ix_personalprojection_site_user_id"),
        "personalprojection",
        ["site_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_personalprojection_player_id"),
        "personalprojection",
        ["player_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_personalprojection_season"),
        "personalprojection",
        ["season"],
        unique=False,
    )
    op.create_index(
        op.f("ix_personalprojection_position"),
        "personalprojection",
        ["position"],
        unique=False,
    )

    op.create_table(
        "personalprojectionoutcome",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("projection_id", sa.Integer(), nullable=False),
        sa.Column("outcome_index", sa.Integer(), nullable=False),
        sa.Column("position_rank", sa.Integer(), nullable=False),
        sa.Column("probability", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["projection_id"], ["personalprojection.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "projection_id",
            "outcome_index",
            name="uq_personalprojectionoutcome_projection_index",
        ),
    )
    op.create_index(
        op.f("ix_personalprojectionoutcome_projection_id"),
        "personalprojectionoutcome",
        ["projection_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_personalprojectionoutcome_position_rank"),
        "personalprojectionoutcome",
        ["position_rank"],
        unique=False,
    )

    op.create_table(
        "personalrankcurve",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("settings_fingerprint", sa.String(), nullable=False),
        sa.Column("total_rosters", sa.Integer(), nullable=False),
        sa.Column("scoring_settings", sa.JSON(), nullable=False),
        sa.Column("roster_positions", sa.JSON(), nullable=False),
        sa.Column("season_start", sa.Integer(), nullable=False),
        sa.Column("season_end", sa.Integer(), nullable=False),
        sa.Column("position", sa.String(), nullable=False),
        sa.Column("rank_value", sa.Integer(), nullable=False),
        sa.Column("rank_band_start", sa.Integer(), nullable=False),
        sa.Column("rank_band_end", sa.Integer(), nullable=False),
        sa.Column("sample_size", sa.Integer(), nullable=False),
        sa.Column("avg_redraft_starter_war", sa.Float(), nullable=False),
        sa.Column("avg_redraft_roster_war", sa.Float(), nullable=False),
        sa.Column("curve_version", sa.String(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "settings_fingerprint",
            "position",
            "rank_value",
            "curve_version",
            name="uq_personalrankcurve_fingerprint_position_rank_version",
        ),
    )
    op.create_index(
        op.f("ix_personalrankcurve_settings_fingerprint"),
        "personalrankcurve",
        ["settings_fingerprint"],
        unique=False,
    )
    op.create_index(
        op.f("ix_personalrankcurve_position"),
        "personalrankcurve",
        ["position"],
        unique=False,
    )
    op.create_index(
        op.f("ix_personalrankcurve_rank_value"),
        "personalrankcurve",
        ["rank_value"],
        unique=False,
    )
    op.create_index(
        op.f("ix_personalrankcurve_season_start"),
        "personalrankcurve",
        ["season_start"],
        unique=False,
    )
    op.create_index(
        op.f("ix_personalrankcurve_season_end"),
        "personalrankcurve",
        ["season_end"],
        unique=False,
    )
    op.create_index(
        op.f("ix_personalrankcurve_curve_version"),
        "personalrankcurve",
        ["curve_version"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_personalrankcurve_curve_version"), table_name="personalrankcurve")
    op.drop_index(op.f("ix_personalrankcurve_season_end"), table_name="personalrankcurve")
    op.drop_index(op.f("ix_personalrankcurve_season_start"), table_name="personalrankcurve")
    op.drop_index(op.f("ix_personalrankcurve_rank_value"), table_name="personalrankcurve")
    op.drop_index(op.f("ix_personalrankcurve_position"), table_name="personalrankcurve")
    op.drop_index(op.f("ix_personalrankcurve_settings_fingerprint"), table_name="personalrankcurve")
    op.drop_table("personalrankcurve")

    op.drop_index(op.f("ix_personalprojectionoutcome_position_rank"), table_name="personalprojectionoutcome")
    op.drop_index(op.f("ix_personalprojectionoutcome_projection_id"), table_name="personalprojectionoutcome")
    op.drop_table("personalprojectionoutcome")

    op.drop_index(op.f("ix_personalprojection_position"), table_name="personalprojection")
    op.drop_index(op.f("ix_personalprojection_season"), table_name="personalprojection")
    op.drop_index(op.f("ix_personalprojection_player_id"), table_name="personalprojection")
    op.drop_index(op.f("ix_personalprojection_site_user_id"), table_name="personalprojection")
    op.drop_table("personalprojection")
