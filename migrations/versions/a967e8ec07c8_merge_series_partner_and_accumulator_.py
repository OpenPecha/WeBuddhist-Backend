"""merge series_partner and accumulator/shareable heads

Revision ID: a967e8ec07c8
Revises: f0eab4237ef7, z2a3b4c5d6e7
Create Date: 2026-06-27 12:59:50.152154

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a967e8ec07c8'
down_revision: Union[str, None] = ('f0eab4237ef7', 'z2a3b4c5d6e7')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
