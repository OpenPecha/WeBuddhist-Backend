"""add deleted_at to group_accumulators

Revision ID: 3f8e9d2c1b0a
Revises: 815f69f1fc54
Create Date: 2026-06-29 22:22:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3f8e9d2c1b0a'
down_revision: Union[str, None] = '815f69f1fc54'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "group_accumulators",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("group_accumulators", "deleted_at")
