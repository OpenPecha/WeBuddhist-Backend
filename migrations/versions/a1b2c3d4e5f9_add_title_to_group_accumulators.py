"""add title to group_accumulators

Revision ID: a1b2c3d4e5f9
Revises: 3f8e9d2c1b0a
Create Date: 2026-06-30 11:43:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f9'
down_revision: Union[str, None] = '3f8e9d2c1b0a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "group_accumulators",
        sa.Column("title", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("group_accumulators", "title")
