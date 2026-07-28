"""add_group_post_comments_table

Revision ID: gp2b3c4d5e6f
Revises: gp1a2b3c4d5e
Create Date: 2026-07-27 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'gp2b3c4d5e6f'
down_revision: Union[str, None] = 'gp1a2b3c4d5e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'group_post_comments',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('post_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['post_id'], ['group_posts.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_group_post_comments_post_id', 'group_post_comments', ['post_id'], unique=False)
    op.create_index('idx_group_post_comments_user_id', 'group_post_comments', ['user_id'], unique=False)
    op.create_index(
        'idx_group_post_comments_feed',
        'group_post_comments',
        ['post_id', sa.text('created_at DESC'), sa.text('id DESC')],
        unique=False,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index('idx_group_post_comments_feed', table_name='group_post_comments')
    op.drop_index('idx_group_post_comments_user_id', table_name='group_post_comments')
    op.drop_index('idx_group_post_comments_post_id', table_name='group_post_comments')
    op.drop_table('group_post_comments')
