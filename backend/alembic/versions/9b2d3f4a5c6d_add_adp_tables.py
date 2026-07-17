"""add adp tables

Revision ID: 9b2d3f4a5c6d
Revises: b4e2a11dc1be
Create Date: 2026-07-17 11:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9b2d3f4a5c6d"
down_revision: Union[str, Sequence[str], None] = "b4e2a11dc1be"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "adpdiscoverynode",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("node_type", sa.String(), nullable=False),
        sa.Column("node_value", sa.String(), nullable=False),
        sa.Column("source_type", sa.String(), nullable=True),
        sa.Column("source_value", sa.String(), nullable=True),
        sa.Column("discovery_depth", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("next_retry_at", sa.DateTime(), nullable=True),
        sa.Column("last_checked_at", sa.DateTime(), nullable=True),
        sa.Column("failure_reason", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_adpdiscoverynode_node_type"),
        "adpdiscoverynode",
        ["node_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_adpdiscoverynode_node_value"),
        "adpdiscoverynode",
        ["node_value"],
        unique=False,
    )
    op.create_index(
        op.f("ix_adpdiscoverynode_discovery_depth"),
        "adpdiscoverynode",
        ["discovery_depth"],
        unique=False,
    )
    op.create_index(
        op.f("ix_adpdiscoverynode_status"),
        "adpdiscoverynode",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_adpdiscoverynode_next_retry_at"),
        "adpdiscoverynode",
        ["next_retry_at"],
        unique=False,
    )
    op.create_index(
        "ix_adpdiscoverynode_type_value",
        "adpdiscoverynode",
        ["node_type", "node_value"],
        unique=True,
    )

    op.create_table(
        "adpdraftqualification",
        sa.Column("draft_id", sa.String(), nullable=False),
        sa.Column("league_id", sa.String(), nullable=True),
        sa.Column("draft_started_at", sa.DateTime(), nullable=True),
        sa.Column("draft_completed_at", sa.DateTime(), nullable=True),
        sa.Column("draft_kind", sa.String(), nullable=False),
        sa.Column("league_format", sa.String(), nullable=False),
        sa.Column("qb_format", sa.String(), nullable=False),
        sa.Column("te_premium", sa.String(), nullable=False),
        sa.Column("scoring_format", sa.String(), nullable=False),
        sa.Column("team_count", sa.Integer(), nullable=True),
        sa.Column("round_count", sa.Integer(), nullable=True),
        sa.Column("is_mock", sa.Boolean(), nullable=False),
        sa.Column("is_complete", sa.Boolean(), nullable=False),
        sa.Column("is_qualified", sa.Boolean(), nullable=False),
        sa.Column("qualification_code", sa.String(), nullable=False),
        sa.Column("qualification_details", sa.JSON(), nullable=False),
        sa.Column("classified_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["draft_id"], ["draft.draft_id"]),
        sa.ForeignKeyConstraint(["league_id"], ["league.league_id"]),
        sa.PrimaryKeyConstraint("draft_id"),
    )
    op.create_index(
        op.f("ix_adpdraftqualification_league_id"),
        "adpdraftqualification",
        ["league_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_adpdraftqualification_draft_started_at"),
        "adpdraftqualification",
        ["draft_started_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_adpdraftqualification_draft_completed_at"),
        "adpdraftqualification",
        ["draft_completed_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_adpdraftqualification_draft_kind"),
        "adpdraftqualification",
        ["draft_kind"],
        unique=False,
    )
    op.create_index(
        op.f("ix_adpdraftqualification_league_format"),
        "adpdraftqualification",
        ["league_format"],
        unique=False,
    )
    op.create_index(
        op.f("ix_adpdraftqualification_qb_format"),
        "adpdraftqualification",
        ["qb_format"],
        unique=False,
    )
    op.create_index(
        op.f("ix_adpdraftqualification_te_premium"),
        "adpdraftqualification",
        ["te_premium"],
        unique=False,
    )
    op.create_index(
        op.f("ix_adpdraftqualification_scoring_format"),
        "adpdraftqualification",
        ["scoring_format"],
        unique=False,
    )
    op.create_index(
        op.f("ix_adpdraftqualification_team_count"),
        "adpdraftqualification",
        ["team_count"],
        unique=False,
    )
    op.create_index(
        op.f("ix_adpdraftqualification_is_qualified"),
        "adpdraftqualification",
        ["is_qualified"],
        unique=False,
    )
    op.create_index(
        op.f("ix_adpdraftqualification_qualification_code"),
        "adpdraftqualification",
        ["qualification_code"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_adpdraftqualification_qualification_code"),
        table_name="adpdraftqualification",
    )
    op.drop_index(
        op.f("ix_adpdraftqualification_is_qualified"),
        table_name="adpdraftqualification",
    )
    op.drop_index(
        op.f("ix_adpdraftqualification_team_count"),
        table_name="adpdraftqualification",
    )
    op.drop_index(
        op.f("ix_adpdraftqualification_scoring_format"),
        table_name="adpdraftqualification",
    )
    op.drop_index(
        op.f("ix_adpdraftqualification_te_premium"),
        table_name="adpdraftqualification",
    )
    op.drop_index(
        op.f("ix_adpdraftqualification_qb_format"),
        table_name="adpdraftqualification",
    )
    op.drop_index(
        op.f("ix_adpdraftqualification_league_format"),
        table_name="adpdraftqualification",
    )
    op.drop_index(
        op.f("ix_adpdraftqualification_draft_kind"),
        table_name="adpdraftqualification",
    )
    op.drop_index(
        op.f("ix_adpdraftqualification_draft_completed_at"),
        table_name="adpdraftqualification",
    )
    op.drop_index(
        op.f("ix_adpdraftqualification_draft_started_at"),
        table_name="adpdraftqualification",
    )
    op.drop_index(
        op.f("ix_adpdraftqualification_league_id"),
        table_name="adpdraftqualification",
    )
    op.drop_table("adpdraftqualification")

    op.drop_index(
        "ix_adpdiscoverynode_type_value",
        table_name="adpdiscoverynode",
    )
    op.drop_index(
        op.f("ix_adpdiscoverynode_next_retry_at"),
        table_name="adpdiscoverynode",
    )
    op.drop_index(
        op.f("ix_adpdiscoverynode_status"),
        table_name="adpdiscoverynode",
    )
    op.drop_index(
        op.f("ix_adpdiscoverynode_discovery_depth"),
        table_name="adpdiscoverynode",
    )
    op.drop_index(
        op.f("ix_adpdiscoverynode_node_value"),
        table_name="adpdiscoverynode",
    )
    op.drop_index(
        op.f("ix_adpdiscoverynode_node_type"),
        table_name="adpdiscoverynode",
    )
    op.drop_table("adpdiscoverynode")
