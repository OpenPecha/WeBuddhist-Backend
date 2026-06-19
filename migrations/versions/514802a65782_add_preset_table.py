"""add_preset_table

Revision ID: 514802a65782
Revises: 888b759bcd6a
Create Date: 2026-06-18 22:49:49.758709

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '514802a65782'
down_revision: Union[str, None] = '888b759bcd6a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'preset_table',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('subtask_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('version_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('language', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by', sa.String(length=255), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_by', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['subtask_id'], ['sub_tasks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('subtask_id')
    )
    op.create_index('idx_preset_subtask_id', 'preset_table', ['subtask_id'])
    op.create_index('idx_preset_version_id', 'preset_table', ['version_id'])


def downgrade() -> None:
    op.drop_index('idx_preset_version_id', table_name='preset_table')
    op.drop_index('idx_preset_subtask_id', table_name='preset_table')
    op.drop_table('preset_table')
