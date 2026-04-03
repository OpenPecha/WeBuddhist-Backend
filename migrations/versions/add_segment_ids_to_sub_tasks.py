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
    # 1. Add segment_ids column as UUID array to support multiple segment references
    op.add_column('sub_tasks', sa.Column('segment_ids', postgresql.ARRAY(sa.UUID()), nullable=True, server_default='{}'))
    
    # 2. Migrate existing segment_id data to segment_ids array
    # This transfers all existing SOURCE_REFERENCE segment_id values to the new array column
    op.execute("""
        UPDATE sub_tasks 
        SET segment_ids = ARRAY[segment_id]::uuid[] 
        WHERE segment_id IS NOT NULL
    """)
    
    # 3. Drop the old segment_id column
    op.drop_column('sub_tasks', 'segment_id')


def downgrade() -> None:
    # 1. Re-add segment_id column
    op.add_column('sub_tasks', sa.Column('segment_id', sa.UUID(), nullable=True))
    
    # 2. Migrate first element of segment_ids back to segment_id
    # Note: This will lose data if there are multiple segments - only first one is kept
    op.execute("""
        UPDATE sub_tasks 
        SET segment_id = segment_ids[1] 
        WHERE segment_ids IS NOT NULL AND array_length(segment_ids, 1) > 0
    """)
    
    # 3. Drop segment_ids column
    op.drop_column('sub_tasks', 'segment_ids')
