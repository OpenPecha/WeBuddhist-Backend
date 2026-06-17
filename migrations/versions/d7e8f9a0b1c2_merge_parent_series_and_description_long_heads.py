"""merge parent_series_id and description_long heads

Revision ID: d7e8f9a0b1c2
Revises: c5d6e7f8a9b0, c6d7e8f9a0b1
Create Date: 2026-06-16 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d7e8f9a0b1c2"
down_revision: Union[str, Sequence[str], None] = ("c5d6e7f8a9b0", "c6d7e8f9a0b1")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
