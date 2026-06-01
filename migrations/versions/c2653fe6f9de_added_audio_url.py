"""added audio_url

Revision ID: c2653fe6f9de
Revises: ecccb9c7779b
Create Date: 2026-05-30 16:05:03.293964

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c2653fe6f9de'
down_revision: Union[str, None] = 'ecccb9c7779b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    from sqlalchemy import inspect
    
    bind = op.get_bind()
    inspector = inspect(bind)
    
    def constraint_exists(table_name: str, constraint_name: str) -> bool:
        result = bind.execute(sa.text(
            f"SELECT COUNT(*) FROM pg_constraint WHERE conname = :name AND conrelid = '{table_name}'::regclass"
        ), {"name": constraint_name})
        return result.scalar() > 0
    
    # Drop indexes only if they exist
    existing_indexes = {idx['name'] for idx in inspector.get_indexes('author_group_followers')}
    if 'idx_author_group_followers_group_user' in existing_indexes:
        op.drop_index('idx_author_group_followers_group_user', table_name='author_group_followers')
    
    # Create unique constraint only if it doesn't exist (check for PRIMARY KEY too)
    if not constraint_exists('author_group_followers', 'uq_author_group_followers_group_user'):
        op.create_unique_constraint('uq_author_group_followers_group_user', 'author_group_followers', ['group_id', 'user_id'])
    
    # Handle author_group_plans
    existing_indexes = {idx['name'] for idx in inspector.get_indexes('author_group_plans')}
    if 'idx_author_group_plans_group_plan' in existing_indexes:
        op.drop_index('idx_author_group_plans_group_plan', table_name='author_group_plans')
    
    if not constraint_exists('author_group_plans', 'uq_author_group_plans_group_plan'):
        op.create_unique_constraint('uq_author_group_plans_group_plan', 'author_group_plans', ['group_id', 'plan_id'])
    
    # Handle author_group_series
    existing_indexes = {idx['name'] for idx in inspector.get_indexes('author_group_series')}
    if 'idx_author_group_series_group_series' in existing_indexes:
        op.drop_index('idx_author_group_series_group_series', table_name='author_group_series')
    
    if not constraint_exists('author_group_series', 'uq_author_group_series_group_series'):
        op.create_unique_constraint('uq_author_group_series_group_series', 'author_group_series', ['group_id', 'series_id'])
    
    # Handle author_group_tags
    existing_indexes = {idx['name'] for idx in inspector.get_indexes('author_group_tags')}
    if 'idx_author_group_tags_group_tag' in existing_indexes:
        op.drop_index('idx_author_group_tags_group_tag', table_name='author_group_tags')
    
    if not constraint_exists('author_group_tags', 'uq_author_group_tags_group_tag'):
        op.create_unique_constraint('uq_author_group_tags_group_tag', 'author_group_tags', ['group_id', 'tag_id'])
    
    # Handle plans search index
    existing_indexes = {idx['name'] for idx in inspector.get_indexes('plans')}
    if 'idx_plans_search' in existing_indexes:
        op.drop_index('idx_plans_search', table_name='plans', postgresql_using='gin')
    op.create_index('idx_plans_search', 'plans', [sa.text("to_tsvector('english', title || ' ' || COALESCE(description, ''))")], unique=False, postgresql_using='gin')
    
    # Add audio_url column
    op.add_column('sub_tasks', sa.Column('audio_url', sa.String(length=255), nullable=True))


def downgrade() -> None:
    from sqlalchemy import inspect
    
    bind = op.get_bind()
    inspector = inspect(bind)
    
    def constraint_exists(table_name: str, constraint_name: str) -> bool:
        result = bind.execute(sa.text(
            f"SELECT COUNT(*) FROM pg_constraint WHERE conname = :name AND conrelid = '{table_name}'::regclass"
        ), {"name": constraint_name})
        return result.scalar() > 0
    
    # Drop audio_url column
    op.drop_column('sub_tasks', 'audio_url')
    
    # Handle plans search index
    existing_indexes = {idx['name'] for idx in inspector.get_indexes('plans')}
    if 'idx_plans_search' in existing_indexes:
        op.drop_index('idx_plans_search', table_name='plans', postgresql_using='gin')
    op.create_index('idx_plans_search', 'plans', [sa.text("to_tsvector('english'::regconfig, (title::text || ' '::text) || COALESCE(description, ''::text))")], unique=False, postgresql_using='gin')
    
    # Handle author_group_tags
    if constraint_exists('author_group_tags', 'uq_author_group_tags_group_tag'):
        op.drop_constraint('uq_author_group_tags_group_tag', 'author_group_tags', type_='unique')
    
    existing_indexes = {idx['name'] for idx in inspector.get_indexes('author_group_tags')}
    if 'idx_author_group_tags_group_tag' not in existing_indexes:
        op.create_index('idx_author_group_tags_group_tag', 'author_group_tags', ['group_id', 'tag_id'], unique=False)
    
    # Handle author_group_series
    if constraint_exists('author_group_series', 'uq_author_group_series_group_series'):
        op.drop_constraint('uq_author_group_series_group_series', 'author_group_series', type_='unique')
    
    existing_indexes = {idx['name'] for idx in inspector.get_indexes('author_group_series')}
    if 'idx_author_group_series_group_series' not in existing_indexes:
        op.create_index('idx_author_group_series_group_series', 'author_group_series', ['group_id', 'series_id'], unique=False)
    
    # Handle author_group_plans
    if constraint_exists('author_group_plans', 'uq_author_group_plans_group_plan'):
        op.drop_constraint('uq_author_group_plans_group_plan', 'author_group_plans', type_='unique')
    
    existing_indexes = {idx['name'] for idx in inspector.get_indexes('author_group_plans')}
    if 'idx_author_group_plans_group_plan' not in existing_indexes:
        op.create_index('idx_author_group_plans_group_plan', 'author_group_plans', ['group_id', 'plan_id'], unique=False)
    
    # Handle author_group_followers
    if constraint_exists('author_group_followers', 'uq_author_group_followers_group_user'):
        op.drop_constraint('uq_author_group_followers_group_user', 'author_group_followers', type_='unique')
    
    existing_indexes = {idx['name'] for idx in inspector.get_indexes('author_group_followers')}
    if 'idx_author_group_followers_group_user' not in existing_indexes:
        op.create_index('idx_author_group_followers_group_user', 'author_group_followers', ['group_id', 'user_id'], unique=False)
