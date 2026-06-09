"""add recitation_collection session type to enum

Revision ID: 503196734168
Revises: 402085623057
Create Date: 2025-11-12 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '503196734168'
down_revision: Union[str, None] = '402085623057'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add RECITATION_COLLECTION to the sessiontype enum
    op.execute("ALTER TYPE sessiontype ADD VALUE IF NOT EXISTS 'RECITATION_COLLECTION'")


def downgrade() -> None:
    # Note: PostgreSQL doesn't support removing enum values directly
    # This would require recreating the enum type and all dependent columns
    # For safety, we leave the enum value in place during downgrade
    pass
