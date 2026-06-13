"""add_verse_metadata_table

Revision ID: d1e2f3a4b5c6
Revises: 5cd30a42ee8b
Create Date: 2026-06-13 11:47:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'd1e2f3a4b5c6'
down_revision: Union[str, None] = '2e73e46c9349'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create verse_metadata table
    op.create_table('verse_metadata',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('verse_of_day_id', sa.UUID(), nullable=False),
        sa.Column('verse', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('lang', sa.String(length=10), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['verse_of_day_id'], ['verse_of_day.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('verse_of_day_id', 'lang', name='uq_verse_metadata_verse_of_day_lang')
    )
    op.create_index('idx_verse_metadata_verse_of_day_id', 'verse_metadata', ['verse_of_day_id'], unique=False)
    op.create_index('idx_verse_metadata_lang', 'verse_metadata', ['lang'], unique=False)
    
    # Drop verse column from verse_of_day table
    op.drop_column('verse_of_day', 'verse')


def downgrade() -> None:
    # First, add verse column back to verse_of_day table (with server_default to handle existing rows)
    op.add_column('verse_of_day', sa.Column('verse', sa.Text(), nullable=False, server_default=''))
    
    # Remove the server_default since original column didn't have one
    op.alter_column('verse_of_day', 'verse', server_default=None)
    
    # Then drop verse_metadata table (indexes will be dropped automatically with table)
    op.drop_index('idx_verse_metadata_lang', table_name='verse_metadata')
    op.drop_index('idx_verse_metadata_verse_of_day_id', table_name='verse_metadata')
    op.drop_table('verse_metadata')
