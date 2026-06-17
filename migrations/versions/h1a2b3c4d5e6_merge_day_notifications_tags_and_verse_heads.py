"""merge tags display_order and verse_metadata heads

Revision ID: h1a2b3c4d5e6
Revises: f9a0b1c2d3e5, g0a1b2c3d4e5
Create Date: 2026-06-17 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "h1a2b3c4d5e6"
down_revision: Union[str, Sequence[str], None] = ("f9a0b1c2d3e5", "g0a1b2c3d4e5")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
