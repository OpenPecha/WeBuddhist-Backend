"""add_timer_history_table

Revision ID: 2e73e46c9349
Revises: a1b2c3d4e5f8
Create Date: 2026-06-12 10:47:15.959561

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2e73e46c9349'
down_revision: Union[str, None] = 'a1b2c3d4e5f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('timer_history',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('timer_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('duration', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['timer_id'], ['timers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_timer_history_timer_id', 'timer_history', ['timer_id'], unique=False)
    op.create_index('idx_timer_history_user_id', 'timer_history', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_timer_history_user_id', table_name='timer_history')
    op.drop_index('idx_timer_history_timer_id', table_name='timer_history')
    op.drop_table('timer_history')
