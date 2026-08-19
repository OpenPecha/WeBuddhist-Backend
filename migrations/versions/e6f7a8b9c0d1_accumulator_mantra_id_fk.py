"""accumulator_mantra_id_fk

Turn accumulators.mantra_id into a real foreign key referencing mantra.id with
ON DELETE SET NULL, so the DB enforces the link and nulls it out if the mantra
is deleted. Adds a supporting index on the column.

Revision ID: e6f7a8b9c0d1
Revises: d5e6f7a8b9c0
Create Date: 2026-06-13 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = 'e6f7a8b9c0d1'
down_revision: Union[str, None] = 'd5e6f7a8b9c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index('idx_accumulators_mantra_id', 'accumulators', ['mantra_id'])
    op.create_foreign_key(
        'accumulators_mantra_id_fkey',
        'accumulators',
        'mantra',
        ['mantra_id'],
        ['id'],
        ondelete='SET NULL',
    )


def downgrade() -> None:
    op.drop_constraint('accumulators_mantra_id_fkey', 'accumulators', type_='foreignkey')
    op.drop_index('idx_accumulators_mantra_id', table_name='accumulators')
