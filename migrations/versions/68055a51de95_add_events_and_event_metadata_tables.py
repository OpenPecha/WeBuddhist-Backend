"""add_events_and_event_metadata_tables

Revision ID: 68055a51de95
Revises: b7c8d9e0f1a2
Create Date: 2026-06-12 22:11:20.409966

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '68055a51de95'
down_revision: Union[str, None] = 'b7c8d9e0f1a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'events',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('plan_id', sa.UUID(), nullable=True),
        sa.Column('accumulator_id', sa.UUID(), nullable=True),
        sa.Column('mantra_id', sa.UUID(), nullable=True),
        sa.Column('timer_id', sa.UUID(), nullable=True),
        sa.Column('group_id', sa.UUID(), nullable=False),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by', sa.String(length=255), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['accumulator_id'], ['accumulators.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['group_id'], ['author_groups.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['mantra_id'], ['mantra.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['plan_id'], ['plans.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['timer_id'], ['timers.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_events_end_date', 'events', ['end_date'], unique=False)
    op.create_index('idx_events_group_id', 'events', ['group_id'], unique=False)
    op.create_index('idx_events_start_date', 'events', ['start_date'], unique=False)

    op.create_table(
        'event_metadata',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('event_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column(
            'language',
            postgresql.ENUM('EN', 'BO', 'ZH', name='languagecode', create_type=False),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('event_id', 'language', name='uq_event_metadata_event_language'),
    )
    op.create_index(
        'idx_event_metadata_event_language',
        'event_metadata',
        ['event_id', 'language'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index('idx_event_metadata_event_language', table_name='event_metadata')
    op.drop_table('event_metadata')
    op.drop_index('idx_events_start_date', table_name='events')
    op.drop_index('idx_events_group_id', table_name='events')
    op.drop_index('idx_events_end_date', table_name='events')
    op.drop_table('events')
