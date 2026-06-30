"""merge_group_accumulator_and_series_backfill

Revision ID: 31ed800a4c85
Revises: 2da1ef4d53a3, c7d8e9f0a1b2
Create Date: 2026-06-30 12:37:03.629795

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '31ed800a4c85'
down_revision: Union[str, None] = ('2da1ef4d53a3', 'c7d8e9f0a1b2')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
