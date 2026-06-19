"""add_ref_id_to_verse_of_day

Revision ID: b2c3d4e5f6a8
Revises: a1b2c3d4e5f7
Create Date: 2026-06-05 15:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision: str = 'b2c3d4e5f6a8'
down_revision: Union[str, None] = 'a1b2c3d4e5f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(table: str, column: str) -> bool:
    columns = {col["name"] for col in inspect(op.get_bind()).get_columns(table)}
    return column in columns


def upgrade() -> None:
    if _column_exists('verse_of_day', 'ref_id'):
        return
    op.add_column('verse_of_day', sa.Column('ref_id', sa.String(length=255), nullable=False))


def downgrade() -> None:
    op.drop_column('verse_of_day', 'ref_id')
