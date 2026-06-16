"""make verse_of_day verse_id, ref_id, ref_type nullable

Revision ID: e8f9a0b1c2d3
Revises: d7e8f9a0b1c2
Create Date: 2026-06-16 23:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e8f9a0b1c2d3"
down_revision: Union[str, None] = "d7e8f9a0b1c2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('verse_of_day', 'verse_id',
                    existing_type=sa.String(length=255),
                    nullable=True)
    op.alter_column('verse_of_day', 'ref_id',
                    existing_type=sa.String(length=255),
                    nullable=True)
    op.alter_column('verse_of_day', 'ref_type',
                    existing_type=sa.String(length=50),
                    nullable=True)


def downgrade() -> None:
    op.alter_column('verse_of_day', 'ref_type',
                    existing_type=sa.String(length=50),
                    nullable=False)
    op.alter_column('verse_of_day', 'ref_id',
                    existing_type=sa.String(length=255),
                    nullable=False)
    op.alter_column('verse_of_day', 'verse_id',
                    existing_type=sa.String(length=255),
                    nullable=False)
