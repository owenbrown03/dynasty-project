"""add projection stats

Revision ID: 9e4ec89deba2
Revises: 59a40d83bc88
Create Date: 2026-06-29 22:13:34.630238

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel



# revision identifiers, used by Alembic.
revision: str = '9e4ec89deba2'
down_revision: Union[str, Sequence[str], None] = '59a40d83bc88'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.add_column(
        "playerprojection",
        sa.Column(
            "pass_att",
            sa.Float(),
            nullable=False,
            server_default="0",
        ),
    )

    op.add_column(
        "playerprojection",
        sa.Column(
            "pass_cmp",
            sa.Float(),
            nullable=False,
            server_default="0",
        ),
    )

    op.add_column(
        "playerprojection",
        sa.Column(
            "pass_yd",
            sa.Float(),
            nullable=False,
            server_default="0",
        ),
    )

    op.add_column(
        "playerprojection",
        sa.Column(
            "pass_td",
            sa.Float(),
            nullable=False,
            server_default="0",
        ),
    )

    op.add_column(
        "playerprojection",
        sa.Column(
            "pass_int",
            sa.Float(),
            nullable=False,
            server_default="0",
        ),
    )

    op.add_column(
        "playerprojection",
        sa.Column(
            "pass_2pt",
            sa.Float(),
            nullable=False,
            server_default="0",
        ),
    )

    op.add_column(
        "playerprojection",
        sa.Column(
            "rush_att",
            sa.Float(),
            nullable=False,
            server_default="0",
        ),
    )

    op.add_column(
        "playerprojection",
        sa.Column(
            "rush_yd",
            sa.Float(),
            nullable=False,
            server_default="0",
        ),
    )

    op.add_column(
        "playerprojection",
        sa.Column(
            "rush_td",
            sa.Float(),
            nullable=False,
            server_default="0",
        ),
    )

    op.add_column(
        "playerprojection",
        sa.Column(
            "rush_2pt",
            sa.Float(),
            nullable=False,
            server_default="0",
        ),
    )

    op.add_column(
        "playerprojection",
        sa.Column(
            "rec",
            sa.Float(),
            nullable=False,
            server_default="0",
        ),
    )

    op.add_column(
        "playerprojection",
        sa.Column(
            "rec_yd",
            sa.Float(),
            nullable=False,
            server_default="0",
        ),
    )

    op.add_column(
        "playerprojection",
        sa.Column(
            "rec_td",
            sa.Float(),
            nullable=False,
            server_default="0",
        ),
    )

    op.add_column(
        "playerprojection",
        sa.Column(
            "rec_2pt",
            sa.Float(),
            nullable=False,
            server_default="0",
        ),
    )

    op.add_column(
        "playerprojection",
        sa.Column(
            "fum_lost",
            sa.Float(),
            nullable=False,
            server_default="0",
        ),
    )

    op.add_column(
        "playerprojection",
        sa.Column(
            "pass_fd",
            sa.Float(),
            nullable=False,
            server_default="0",
        ),
    )

    op.add_column(
        "playerprojection",
        sa.Column(
            "rush_fd",
            sa.Float(),
            nullable=False,
            server_default="0",
        ),
    )

    op.add_column(
        "playerprojection",
        sa.Column(
            "rec_fd",
            sa.Float(),
            nullable=False,
            server_default="0",
        ),
    )

    op.add_column(
        "playerprojection",
        sa.Column(
            "rec_0_4",
            sa.Float(),
            nullable=False,
            server_default="0",
        ),
    )

    op.add_column(
        "playerprojection",
        sa.Column(
            "rec_5_9",
            sa.Float(),
            nullable=False,
            server_default="0",
        ),
    )

    op.add_column(
        "playerprojection",
        sa.Column(
            "rec_10_19",
            sa.Float(),
            nullable=False,
            server_default="0",
        ),
    )

    op.add_column(
        "playerprojection",
        sa.Column(
            "rec_20_29",
            sa.Float(),
            nullable=False,
            server_default="0",
        ),
    )

    op.add_column(
        "playerprojection",
        sa.Column(
            "rec_30_39",
            sa.Float(),
            nullable=False,
            server_default="0",
        ),
    )

    op.add_column(
        "playerprojection",
        sa.Column(
            "rec_40p",
            sa.Float(),
            nullable=False,
            server_default="0",
        ),
    )

    op.add_column(
        "playerprojection",
        sa.Column(
            "bonus_rec_rb",
            sa.Float(),
            nullable=False,
            server_default="0",
        ),
    )

    op.add_column(
        "playerprojection",
        sa.Column(
            "bonus_rec_wr",
            sa.Float(),
            nullable=False,
            server_default="0",
        ),
    )

    op.add_column(
        "playerprojection",
        sa.Column(
            "bonus_rec_te",
            sa.Float(),
            nullable=False,
            server_default="0",
        ),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('playerprojection', sa.Column('projected_points', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False))
    op.add_column('playerprojection', sa.Column('projected_ppg', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=False))
    op.add_column('playerprojection', sa.Column('scoring_format', sa.VARCHAR(), autoincrement=False, nullable=False))
    op.drop_column('playerprojection', 'bonus_rec_te')
    op.drop_column('playerprojection', 'bonus_rec_wr')
    op.drop_column('playerprojection', 'bonus_rec_rb')
    op.drop_column('playerprojection', 'rec_40p')
    op.drop_column('playerprojection', 'rec_30_39')
    op.drop_column('playerprojection', 'rec_20_29')
    op.drop_column('playerprojection', 'rec_10_19')
    op.drop_column('playerprojection', 'rec_5_9')
    op.drop_column('playerprojection', 'rec_0_4')
    op.drop_column('playerprojection', 'rec_fd')
    op.drop_column('playerprojection', 'rush_fd')
    op.drop_column('playerprojection', 'pass_fd')
    op.drop_column('playerprojection', 'fum_lost')
    op.drop_column('playerprojection', 'rec_2pt')
    op.drop_column('playerprojection', 'rec_td')
    op.drop_column('playerprojection', 'rec_yd')
    op.drop_column('playerprojection', 'rec')
    op.drop_column('playerprojection', 'rush_2pt')
    op.drop_column('playerprojection', 'rush_td')
    op.drop_column('playerprojection', 'rush_yd')
    op.drop_column('playerprojection', 'rush_att')
    op.drop_column('playerprojection', 'pass_2pt')
    op.drop_column('playerprojection', 'pass_int')
    op.drop_column('playerprojection', 'pass_td')
    op.drop_column('playerprojection', 'pass_yd')
    op.drop_column('playerprojection', 'pass_cmp')
    op.drop_column('playerprojection', 'pass_att')
    # ### end Alembic commands ###

    for column in [
        "pass_att",
        "pass_cmp",
        "pass_yd",
        "pass_td",
        "pass_int",
        "pass_2pt",
        "rush_att",
        "rush_yd",
        "rush_td",
        "rush_2pt",
        "rec",
        "rec_yd",
        "rec_td",
        "rec_2pt",
        "fum_lost",
        "pass_fd",
        "rush_fd",
        "rec_fd",
        "rec_0_4",
        "rec_5_9",
        "rec_10_19",
        "rec_20_29",
        "rec_30_39",
        "rec_40p",
        "bonus_rec_rb",
        "bonus_rec_wr",
        "bonus_rec_te",
    ]:
        op.alter_column(
            "playerprojection",
            column,
            server_default=None,
        )