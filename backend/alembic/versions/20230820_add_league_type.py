'''Add nullable 'type' column to league table.

This migration matches the model change in
backend/app/models/db/sleeper/api.py where a new
`type: Optional[str]` field was added to the `League` model.
The column is nullable to preserve backward compatibility
with existing rows.
''' 

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20230820_add_league_type"
# Adjust down_revision to the latest existing migration ID in the repo
# (you may need to update this manually if the history changes)
# Example placeholder below:
down_revision = "771b6bb3cb32"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("league", sa.Column("type", sa.String(), nullable=True))

def downgrade() -> None:
    op.drop_column("league", "type")
