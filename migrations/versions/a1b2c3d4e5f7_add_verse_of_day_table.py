"""add_verse_of_day_table

Revision ID: a1b2c3d4e5f7
Revises: c3d4e5f6a7b8
Create Date: 2026-06-05 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'a1b2c3d4e5f7'
down_revision: Union[str, None] = 'c5e7a9b1d3f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('verse_of_day',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('verse_id', sa.String(length=255), nullable=False),
        sa.Column('verse', sa.Text(), nullable=False),
        sa.Column('ref_type', sa.String(length=50), nullable=False),
        sa.Column('image_urls', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('group_id', sa.UUID(), nullable=True),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by', sa.String(length=255), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_verse_of_day_date', 'verse_of_day', ['date'], unique=True)
    op.create_index('idx_verse_of_day_ref_type', 'verse_of_day', ['ref_type'], unique=False)
    op.create_index('idx_verse_of_day_group_id', 'verse_of_day', ['group_id'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_verse_of_day_group_id', table_name='verse_of_day')
    op.drop_index('idx_verse_of_day_ref_type', table_name='verse_of_day')
    op.drop_index('idx_verse_of_day_date', table_name='verse_of_day')
    op.drop_table('verse_of_day')
