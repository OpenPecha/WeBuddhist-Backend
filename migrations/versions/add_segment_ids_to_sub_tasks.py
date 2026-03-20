"""add segment_ids array column and drop segment_id from sub_tasks

Revision ID: a7b8c9d0e1f2
Revises: 9984d31f026b
Create Date: 2026-03-19 10:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'a7b8c9d0e1f2'
down_revision: Union[str, None] = '9984d31f026b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add segment_ids column as UUID array to support multiple segment references
    op.add_column('sub_tasks', sa.Column('segment_ids', postgresql.ARRAY(sa.UUID()), nullable=True))
    # Drop the redundant segment_id column (segment_ids array handles both single and multiple)
    op.drop_column('sub_tasks', 'segment_id')


def downgrade() -> None:
    # Re-add segment_id column
    op.add_column('sub_tasks', sa.Column('segment_id', sa.UUID(), nullable=True))
    # Drop segment_ids column
    op.drop_column('sub_tasks', 'segment_ids')
