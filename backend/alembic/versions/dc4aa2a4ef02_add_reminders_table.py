"""add reminders table

Revision ID: dc4aa2a4ef02
Revises: 2730d4f96a91
Create Date: 2026-07-12 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "dc4aa2a4ef02"
down_revision: Union[str, Sequence[str], None] = "2730d4f96a91"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "reminder",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("site_user_id", sa.UUID(), nullable=False),
        sa.Column("league_id", sa.String(), nullable=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("note", sa.String(), nullable=False),
        sa.Column("due_week", sa.Integer(), nullable=True),
        sa.Column("due_season", sa.String(), nullable=True),
        sa.Column("delivery_channel", sa.String(), nullable=False),
        sa.Column("completed", sa.Boolean(), nullable=False),
        sa.Column("email_sent_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["league_id"], ["league.league_id"]),
        sa.ForeignKeyConstraint(["site_user_id"], ["siteuser.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_reminder_site_user_id"), "reminder", ["site_user_id"], unique=False)
    op.create_index(op.f("ix_reminder_league_id"), "reminder", ["league_id"], unique=False)
    op.create_index(op.f("ix_reminder_due_week"), "reminder", ["due_week"], unique=False)
    op.create_index(op.f("ix_reminder_due_season"), "reminder", ["due_season"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_reminder_due_season"), table_name="reminder")
    op.drop_index(op.f("ix_reminder_due_week"), table_name="reminder")
    op.drop_index(op.f("ix_reminder_league_id"), table_name="reminder")
    op.drop_index(op.f("ix_reminder_site_user_id"), table_name="reminder")
    op.drop_table("reminder")
