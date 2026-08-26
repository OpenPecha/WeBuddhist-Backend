"""add_event_links_table

Revision ID: c1d2e3f4a5b7
Revises: b0c1d2e3f4a5
Create Date: 2026-07-23 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from migrations.idempotency import index_exists, table_exists

revision: str = 'c1d2e3f4a5b7'
down_revision: Union[str, None] = 'b0c1d2e3f4a5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if not table_exists('event_links'):
        op.create_table(
            'event_links',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('event_id', sa.UUID(), nullable=False),
            sa.Column('type', sa.String(length=50), nullable=False),
            sa.Column('url', sa.String(length=2000), nullable=False),
            sa.Column('label', sa.String(length=255), nullable=True),
            sa.Column('display_order', sa.Integer(), nullable=False, server_default='1'),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
        )

    if not index_exists('event_links', 'idx_event_links_event_id'):
        op.create_index('idx_event_links_event_id', 'event_links', ['event_id'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_event_links_event_id', table_name='event_links')
    op.drop_table('event_links')
