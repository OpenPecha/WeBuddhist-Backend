"""added new author_id field in series

Revision ID: 2cf7ea29ebbb
Revises: 8a92543236a0
Create Date: 2026-05-06 12:39:19.197251

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2cf7ea29ebbb'
down_revision: Union[str, None] = '8a92543236a0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. Add the author_id column
    op.add_column('series', sa.Column('author_id', sa.UUID(), nullable=False))
    
    # 2. Add the foreign key constraint
    op.create_foreign_key(
        'fk_series_author_id', 
        'series', 
        'authors', 
        ['author_id'], 
        ['id'], 
        ondelete='RESTRICT'
    )

def downgrade() -> None:
    # 1. Drop the foreign key constraint
    op.drop_constraint('fk_series_author_id', 'series', type_='foreignkey')
    
    # 2. Drop the column
    op.drop_column('series', 'author_id')