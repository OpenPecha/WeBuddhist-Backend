"""drop leftover youtube columns from tasks (idempotent)

Some environments reached the head revision with tasks.youtube_url /
tasks.youtube_duration still present (the drop in 44ef04b271d1 did not take
effect there). This migration removes them if they still exist, and is a
no-op where they were already dropped.

Revision ID: r2s3t4u5v6w7
Revises: ce621305e1fb
Create Date: 2026-06-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'r2s3t4u5v6w7'
down_revision: Union[str, None] = 'ce621305e1fb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('ALTER TABLE tasks DROP COLUMN IF EXISTS youtube_duration')
    op.execute('ALTER TABLE tasks DROP COLUMN IF EXISTS youtube_url')


def downgrade() -> None:
    op.add_column('tasks', sa.Column('youtube_url', sa.String(length=255), nullable=True))
    op.add_column('tasks', sa.Column('youtube_duration', sa.String(length=255), nullable=True))
