"""accumulator_group_id_nullable

Make accumulators.group_id nullable. The column is kept for future CMS /
group-preset use, but is no longer supplied by the user-facing endpoints, so
user-created accumulators leave it NULL until a group is assigned.

Revision ID: b4c5d6e7f8a0
Revises: a3b4c5d6e7f9
Create Date: 2026-06-13 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'b4c5d6e7f8a0'
down_revision: Union[str, None] = 'a3b4c5d6e7f9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('accumulators', 'group_id', existing_type=sa.UUID(), nullable=True)


def downgrade() -> None:
    op.alter_column('accumulators', 'group_id', existing_type=sa.UUID(), nullable=False)
