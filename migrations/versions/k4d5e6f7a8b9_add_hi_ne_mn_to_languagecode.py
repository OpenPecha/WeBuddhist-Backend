"""add HI, NE, MN to languagecode enum

Revision ID: k4d5e6f7a8b9
Revises: j3c4d5e6f7a8
Create Date: 2026-06-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'k4d5e6f7a8b9'
down_revision: Union[str, None] = 'j3c4d5e6f7a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add Hindi, Nepali and Mongolian to the languagecode enum.
    # This type backs the `language` column on plans, series_metadata,
    # mantra_metadata, event_metadata and accumulator_metadata.
    op.execute("ALTER TYPE languagecode ADD VALUE IF NOT EXISTS 'HI'")
    op.execute("ALTER TYPE languagecode ADD VALUE IF NOT EXISTS 'NE'")
    op.execute("ALTER TYPE languagecode ADD VALUE IF NOT EXISTS 'MN'")


def downgrade() -> None:
    # Note: PostgreSQL doesn't support removing enum values directly.
    # This would require recreating the enum type and all dependent columns.
    # For safety, we leave the enum values in place during downgrade.
    pass
