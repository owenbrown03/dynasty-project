"""add email verification tables

Revision ID: 0a2d1f8f6d91
Revises: 771b6bb3cb32
Create Date: 2026-07-12 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0a2d1f8f6d91"
down_revision: Union[str, Sequence[str], None] = "771b6bb3cb32"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "siteuser",
        sa.Column(
            "email_verified_at",
            sa.DateTime(),
            nullable=True,
        ),
    )
    op.add_column(
        "siteuser",
        sa.Column(
            "verification_email_sent_at",
            sa.DateTime(),
            nullable=True,
        ),
    )
    op.create_table(
        "emailverificationtoken",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "site_user_id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "token_hash",
            sa.String(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.Column(
            "expires_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.Column(
            "consumed_at",
            sa.DateTime(),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["site_user_id"],
            ["siteuser.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_emailverificationtoken_site_user_id"),
        "emailverificationtoken",
        ["site_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_emailverificationtoken_token_hash"),
        "emailverificationtoken",
        ["token_hash"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_emailverificationtoken_token_hash"),
        table_name="emailverificationtoken",
    )
    op.drop_index(
        op.f("ix_emailverificationtoken_site_user_id"),
        table_name="emailverificationtoken",
    )
    op.drop_table("emailverificationtoken")
    op.drop_column(
        "siteuser",
        "verification_email_sent_at",
    )
    op.drop_column(
        "siteuser",
        "email_verified_at",
    )
