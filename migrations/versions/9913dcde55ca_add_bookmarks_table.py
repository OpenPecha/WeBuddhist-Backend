"""add_bookmarks_table

Revision ID: 9913dcde55ca
Revises: f1a2b3c4d5e6
Create Date: 2026-06-10 10:46:18.447742

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9913dcde55ca'
down_revision: Union[str, None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('bookmarks',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('text_id', sa.UUID(), nullable=False),
        sa.Column('verse_id', sa.String(255), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'text_id', 'verse_id', name='uq_bookmarks_user_text_verse')
    )
    op.create_index('idx_bookmarks_user_id', 'bookmarks', ['user_id'], unique=False)
    op.create_index('idx_bookmarks_text_id', 'bookmarks', ['text_id'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_bookmarks_text_id', table_name='bookmarks')
    op.drop_index('idx_bookmarks_user_id', table_name='bookmarks')
    op.drop_table('bookmarks')
