"""add_group_posts_tables

Revision ID: gp1a2b3c4d5e
Revises: 6f9d6b6333d5
Create Date: 2026-07-27 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'gp1a2b3c4d5e'
down_revision: Union[str, None] = '6f9d6b6333d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _ensure_enum_type(name: str, values: str) -> None:
    op.execute(
        f"DO $$ BEGIN CREATE TYPE {name} AS ENUM ({values}); "
        f"EXCEPTION WHEN duplicate_object THEN NULL; END $$;"
    )


def upgrade() -> None:
    _ensure_enum_type('group_post_status', "'PUBLISHED', 'HIDDEN'")
    _ensure_enum_type('group_post_media_type', "'IMAGE', 'VIDEO', 'AUDIO'")

    group_post_status_enum = postgresql.ENUM(
        'PUBLISHED', 'HIDDEN',
        name='group_post_status',
        create_type=False,
    )
    group_post_media_type_enum = postgresql.ENUM(
        'IMAGE', 'VIDEO', 'AUDIO',
        name='group_post_media_type',
        create_type=False,
    )

    op.create_table(
        'group_posts',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('group_id', sa.UUID(), nullable=False),
        sa.Column('caption', sa.Text(), nullable=True),
        sa.Column('status', group_post_status_enum, nullable=False, server_default='PUBLISHED'),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.String(length=255), nullable=False),
        sa.Column('updated_by', sa.String(length=255), nullable=True),
        sa.Column('deleted_by', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['group_id'], ['author_groups.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_group_posts_group_id', 'group_posts', ['group_id'], unique=False)
    op.create_index(
        'idx_group_posts_feed',
        'group_posts',
        ['group_id', sa.text('published_at DESC'), sa.text('id DESC')],
        unique=False,
        postgresql_where=sa.text("deleted_at IS NULL AND status = 'PUBLISHED'"),
    )

    op.create_table(
        'group_post_media',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('post_id', sa.UUID(), nullable=False),
        sa.Column('media_type', group_post_media_type_enum, nullable=False),
        sa.Column('media_key', sa.String(length=1000), nullable=False),
        sa.Column('thumbnail_key', sa.String(length=1000), nullable=True),
        sa.Column('width', sa.Integer(), nullable=True),
        sa.Column('height', sa.Integer(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('display_order', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['post_id'], ['group_posts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('post_id', 'display_order', name='uq_group_post_media_post_order'),
    )
    op.create_index('idx_group_post_media_post_id', 'group_post_media', ['post_id'], unique=False)

    op.create_table(
        'group_post_links',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('post_id', sa.UUID(), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('url', sa.String(length=2000), nullable=False),
        sa.Column('label', sa.String(length=255), nullable=True),
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['post_id'], ['group_posts.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_group_post_links_post_id', 'group_post_links', ['post_id'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_group_post_links_post_id', table_name='group_post_links')
    op.drop_table('group_post_links')
    op.drop_index('idx_group_post_media_post_id', table_name='group_post_media')
    op.drop_table('group_post_media')
    op.drop_index('idx_group_posts_feed', table_name='group_posts')
    op.drop_index('idx_group_posts_group_id', table_name='group_posts')
    op.drop_table('group_posts')
    op.execute('DROP TYPE IF EXISTS group_post_media_type')
    op.execute('DROP TYPE IF EXISTS group_post_status')
