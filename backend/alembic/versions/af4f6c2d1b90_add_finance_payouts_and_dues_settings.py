"""add finance payouts and dues settings

Revision ID: af4f6c2d1b90
Revises: 8c1af9c43b81
Create Date: 2026-07-12 18:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "af4f6c2d1b90"
down_revision: Union[str, Sequence[str], None] = "8c1af9c43b81"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "commissionerleaguenote",
        sa.Column(
            "paid_years_ahead",
            sa.Integer(),
            nullable=True,
        ),
    )
    op.execute(
        "UPDATE commissionerleaguenote "
        "SET paid_years_ahead = 1 "
        "WHERE paid_years_ahead IS NULL"
    )
    op.alter_column(
        "commissionerleaguenote",
        "paid_years_ahead",
        nullable=False,
        server_default="1",
    )

    op.add_column(
        "financeleagueseason",
        sa.Column(
            "payout_structure",
            sa.JSON(),
            nullable=True,
        ),
    )
    op.execute(
        "UPDATE financeleagueseason "
        "SET payout_structure = '{}'::json "
        "WHERE payout_structure IS NULL"
    )
    op.alter_column(
        "financeleagueseason",
        "payout_structure",
        nullable=False,
        server_default="{}",
    )


def downgrade() -> None:
    op.drop_column(
        "financeleagueseason",
        "payout_structure",
    )
    op.drop_column(
        "commissionerleaguenote",
        "paid_years_ahead",
    )
