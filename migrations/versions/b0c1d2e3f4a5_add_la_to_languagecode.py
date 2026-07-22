"""add LA to languagecode enum

Revision ID: b0c1d2e3f4a5
Revises: a9b0c1d2e3f4
Create Date: 2026-07-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "b0c1d2e3f4a5"
down_revision: Union[str, None] = "a9b0c1d2e3f4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add Ladakhi to the languagecode enum so it matches languages.json.
    # This type backs the `language` column on plans, series_metadata,
    # mantra_metadata, event_metadata, tag_metadata and accumulator_metadata.
    op.execute("ALTER TYPE languagecode ADD VALUE IF NOT EXISTS 'LA'")


def downgrade() -> None:
    # Note: PostgreSQL doesn't support removing enum values directly.
    # This would require recreating the enum type and all dependent columns.
    # For safety, we leave the enum values in place during downgrade.
    pass
