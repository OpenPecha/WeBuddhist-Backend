"""add_poems_table

Revision ID: pm1a2b3c4d5e
Revises: 
Create Date: 2026-08-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'pm1a2b3c4d5e'
down_revision: Union[str, None] = 'ev1a2b3c4d5e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _ensure_enum_type(name: str, values: str) -> None:
    op.execute(
        f"DO $$ BEGIN CREATE TYPE {name} AS ENUM ({values}); "
        f"EXCEPTION WHEN duplicate_object THEN NULL; END $$;"
    )


def upgrade() -> None:
    _ensure_enum_type('poem_status', "'DRAFT', 'PUBLISHED'")

    poem_status_enum = postgresql.ENUM(
        'DRAFT', 'PUBLISHED',
        name='poem_status',
        create_type=False,
    )

    op.create_table(
        'poems',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('author_name', sa.String(length=255), nullable=False),
        sa.Column('chapter_name', sa.String(length=255), nullable=True),
        sa.Column('image_key', sa.String(length=1000), nullable=True),
        sa.Column('status', poem_status_enum, nullable=False, server_default='DRAFT'),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.String(length=255), nullable=False),
        sa.Column('updated_by', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    
    op.create_index(
        'idx_poems_feed',
        'poems',
        [sa.text('published_at DESC'), sa.text('id DESC')],
        unique=False,
        postgresql_where=sa.text("deleted_at IS NULL AND status = 'PUBLISHED'"),
    )
    op.create_index(
        'idx_poems_chapter_name',
        'poems',
        ['chapter_name'],
        unique=False,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        'idx_poems_author_name',
        'poems',
        ['author_name'],
        unique=False,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index('idx_poems_author_name', table_name='poems')
    op.drop_index('idx_poems_chapter_name', table_name='poems')
    op.drop_index('idx_poems_feed', table_name='poems')
    op.drop_table('poems')
    op.execute('DROP TYPE IF EXISTS poem_status')
