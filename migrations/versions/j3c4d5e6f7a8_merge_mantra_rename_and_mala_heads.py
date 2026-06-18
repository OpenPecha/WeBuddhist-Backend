"""merge mantra metadata rename and mala_image heads

Revision ID: j3c4d5e6f7a8
Revises: ffca36f72f3f, i2b3c4d5e6f7
Create Date: 2026-06-17 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "j3c4d5e6f7a8"
down_revision: Union[str, Sequence[str], None] = ("ffca36f72f3f", "i2b3c4d5e6f7")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
