"""add day_videos table

Revision ID: s3t4u5v6w7x8
Revises: r2s3t4u5v6w7
Create Date: 2026-06-19 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 's3t4u5v6w7x8'
down_revision: Union[str, None] = 'r2s3t4u5v6w7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _day_videos_exists() -> bool:
    bind = op.get_bind()
    return bool(
        bind.execute(
            sa.text(
                "SELECT 1 FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_name = 'day_videos'"
            )
        ).fetchone()
    )


def upgrade() -> None:
    if _day_videos_exists():
        return

    op.create_table(
        'day_videos',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('day_id', sa.UUID(), nullable=False),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('video_id', sa.String(length=64), nullable=True),
        sa.Column('title', sa.String(length=500), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by', sa.String(length=255), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['day_id'], ['items.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_index('idx_day_videos_day_id', 'day_videos', ['day_id'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_day_videos_day_id', table_name='day_videos')
    op.drop_table('day_videos')
