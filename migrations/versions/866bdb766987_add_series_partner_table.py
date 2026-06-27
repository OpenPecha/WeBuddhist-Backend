"""add series_partner table

Revision ID: 866bdb766987
Revises: y9z0a1b2c3d4
Create Date: 2026-06-26 21:58:40.627554

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from migrations.idempotency import index_exists, table_exists

# revision identifiers, used by Alembic.
revision: str = '866bdb766987'
down_revision: Union[str, None] = 'y9z0a1b2c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if not table_exists('series_partner'):
        op.create_table(
            'series_partner',
            sa.Column('id', sa.UUID(), nullable=False),
            sa.Column('series_id', sa.UUID(), nullable=False),
            sa.Column('group_id', sa.UUID(), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
            sa.ForeignKeyConstraint(['series_id'], ['series.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['group_id'], ['author_groups.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('series_id', name='uq_series_partner_series'),
        )
    if not index_exists('series_partner', 'idx_series_partner_group'):
        op.create_index('idx_series_partner_group', 'series_partner', ['group_id'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_series_partner_group', table_name='series_partner')
    op.drop_table('series_partner')
