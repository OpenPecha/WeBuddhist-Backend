"""merge timer history rename and series session type heads

Revision ID: n8o9p0q1r2s3
Revises: m6n7o8p9q0r1, m7n8o9p0q1r2
Create Date: 2026-06-18 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "n8o9p0q1r2s3"
down_revision: Union[str, Sequence[str], None] = ("m6n7o8p9q0r1", "m7n8o9p0q1r2")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
