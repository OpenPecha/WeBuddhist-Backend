"""add_event_recurrence_columns

Revision ID: 11de7acad90f
Revises: 6dc5f88f5637
Create Date: 2026-08-14 10:05:29.392294

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '11de7acad90f'
down_revision: Union[str, None] = '6dc5f88f5637'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'events',
        sa.Column('is_recurring', sa.Boolean(), nullable=False, server_default='false')
    )
    op.add_column(
        'events',
        sa.Column('recurrence_frequency', sa.String(length=20), nullable=True)
    )
    op.add_column(
        'events',
        sa.Column('recurrence_date_system', sa.String(length=20), nullable=True)
    )
    op.add_column(
        'events',
        sa.Column('recurrence_calendar_type', sa.String(length=10), nullable=True)
    )
    op.add_column(
        'events',
        sa.Column('recurrence_month', sa.Integer(), nullable=True)
    )
    op.add_column(
        'events',
        sa.Column('recurrence_day', sa.Integer(), nullable=True)
    )
    op.add_column(
        'events',
        sa.Column('duration_days', sa.Integer(), nullable=False, server_default='1')
    )
    
    op.create_check_constraint(
        'ck_events_recurrence_required',
        'events',
        'is_recurring = false OR (recurrence_frequency IS NOT NULL AND recurrence_day IS NOT NULL)'
    )
    op.create_check_constraint(
        'ck_events_lunar_calendar_type',
        'events',
        "recurrence_date_system != 'TIBETAN_LUNAR' OR recurrence_calendar_type IS NOT NULL"
    )
    op.create_check_constraint(
        'ck_events_yearly_month',
        'events',
        "recurrence_frequency != 'YEARLY' OR recurrence_month IS NOT NULL"
    )
    op.create_check_constraint(
        'ck_events_duration_positive',
        'events',
        'duration_days > 0'
    )


def downgrade() -> None:
    op.drop_constraint('ck_events_duration_positive', 'events', type_='check')
    op.drop_constraint('ck_events_yearly_month', 'events', type_='check')
    op.drop_constraint('ck_events_lunar_calendar_type', 'events', type_='check')
    op.drop_constraint('ck_events_recurrence_required', 'events', type_='check')
    
    op.drop_column('events', 'duration_days')
    op.drop_column('events', 'recurrence_day')
    op.drop_column('events', 'recurrence_month')
    op.drop_column('events', 'recurrence_calendar_type')
    op.drop_column('events', 'recurrence_date_system')
    op.drop_column('events', 'recurrence_frequency')
    op.drop_column('events', 'is_recurring')
