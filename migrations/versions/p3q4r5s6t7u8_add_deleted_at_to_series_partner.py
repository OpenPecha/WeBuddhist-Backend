"""add deleted_at to series_partner

Revision ID: p3q4r5s6t7u8
Revises: e1f2a3b4c5d6
Create Date: 2026-07-30 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from migrations.idempotency import column_exists

# revision identifiers, used by Alembic.
revision: str = 'p3q4r5s6t7u8'
down_revision: Union[str, None] = 'e1f2a3b4c5d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if not column_exists('series_partner', 'deleted_at'):
        op.add_column(
            'series_partner',
            sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        )


def downgrade() -> None:
    if column_exists('series_partner', 'deleted_at'):
        op.drop_column('series_partner', 'deleted_at')
