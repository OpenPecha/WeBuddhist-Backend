"""add_mantra_id_to_accumulators

Add an optional mantra_id column to accumulators so an accumulator can reference
a mantra (alongside the existing text_id). Nullable; no FK, matching text_id.

Revision ID: d5e6f7a8b9c0
Revises: b7cb719e3844
Create Date: 2026-06-13 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'd5e6f7a8b9c0'
down_revision: Union[str, None] = 'b7cb719e3844'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('accumulators', sa.Column('mantra_id', sa.UUID(), nullable=True))


def downgrade() -> None:
    op.drop_column('accumulators', 'mantra_id')
