"""merge bookmarks and timers heads

Revision ID: a1b2c3d4e5f8
Revises: f2a3b4c5d6e7, ghxrmguaywg6
Create Date: 2026-06-11 17:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f8"
down_revision: Union[str, Sequence[str], None] = ("f2a3b4c5d6e7", "ghxrmguaywg6")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
