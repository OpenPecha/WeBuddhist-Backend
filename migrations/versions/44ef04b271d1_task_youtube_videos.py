"""create task_youtube_videos and drop task youtube columns

Revision ID: 44ef04b271d1
Revises: n7o8p9q0r1s2
Create Date: 2026-06-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '44ef04b271d1'
down_revision: Union[str, None] = 'n7o8p9q0r1s2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'task_youtube_videos',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('youtube_url', sa.String(length=255), nullable=False),
        sa.Column('display_order', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by', sa.String(length=255), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', sa.String(length=255), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'idx_task_youtube_videos_task_order',
        'task_youtube_videos',
        ['task_id', 'display_order'],
        unique=False,
    )

    # Migrate any existing single-video data into the new table as display_order 1.
    op.execute(
        """
        INSERT INTO task_youtube_videos (id, task_id, youtube_url, display_order, created_at, created_by)
        SELECT gen_random_uuid(), id, youtube_url, 1, COALESCE(created_at, now()), COALESCE(created_by, 'migration')
        FROM tasks
        WHERE youtube_url IS NOT NULL AND youtube_url <> ''
        """
    )

    op.drop_column('tasks', 'youtube_duration')
    op.drop_column('tasks', 'youtube_url')


def downgrade() -> None:
    op.add_column('tasks', sa.Column('youtube_url', sa.String(length=255), nullable=True))
    op.add_column('tasks', sa.Column('youtube_duration', sa.String(length=255), nullable=True))

    # Restore the first video back onto the task (best-effort).
    op.execute(
        """
        UPDATE tasks t
        SET youtube_url = v.youtube_url
        FROM (
            SELECT DISTINCT ON (task_id) task_id, youtube_url
            FROM task_youtube_videos
            ORDER BY task_id, display_order
        ) v
        WHERE t.id = v.task_id
        """
    )

    op.drop_index('idx_task_youtube_videos_task_order', table_name='task_youtube_videos')
    op.drop_table('task_youtube_videos')
