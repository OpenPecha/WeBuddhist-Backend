"""add_youtube_to_tasks

Revision ID: n7o8p9q0r1s2
Revises: m6n7o8p9q0r1
Create Date: 2026-06-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'n7o8p9q0r1s2'
down_revision: Union[str, None] = 'm6n7o8p9q0r1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tasks', sa.Column('youtube_url', sa.String(length=255), nullable=True))
    op.add_column('tasks', sa.Column('youtube_duration', sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column('tasks', 'youtube_duration')
    op.drop_column('tasks', 'youtube_url')
