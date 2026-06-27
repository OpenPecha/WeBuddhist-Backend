"""add series_partner_id to user_series_enrollment

Revision ID: f0eab4237ef7
Revises: 866bdb766987
Create Date: 2026-06-27 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'f0eab4237ef7'
down_revision: Union[str, None] = '866bdb766987'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'user_series_enrollment',
        sa.Column('series_partner_id', sa.UUID(), nullable=True),
    )
    op.create_foreign_key(
        'fk_user_series_enrollment_series_partner',
        'user_series_enrollment',
        'series_partner',
        ['series_partner_id'],
        ['id'],
        ondelete='SET NULL',
    )
    op.create_index(
        'idx_user_series_enrollment_series_partner',
        'user_series_enrollment',
        ['series_partner_id'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index('idx_user_series_enrollment_series_partner', table_name='user_series_enrollment')
    op.drop_constraint('fk_user_series_enrollment_series_partner', 'user_series_enrollment', type_='foreignkey')
    op.drop_column('user_series_enrollment', 'series_partner_id')
