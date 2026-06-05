"""merge platform roles and timer session heads

Revision ID: 020fc79d15bf
Revises: a1b2c3d4e5f7, c5e7a9b1d3f2
Create Date: 2026-06-05 16:19:55.465424
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "020fc79d15bf"
down_revision: Union[str, Sequence[str], None] = ("a1b2c3d4e5f7", "c5e7a9b1d3f2")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
