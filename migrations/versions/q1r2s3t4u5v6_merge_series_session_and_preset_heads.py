"""merge series session and preset heads

Revision ID: q1r2s3t4u5v6
Revises: n8o9p0q1r2s3, p0q1r2s3t4u5
Create Date: 2026-06-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "q1r2s3t4u5v6"
down_revision: Union[str, Sequence[str], None] = ("n8o9p0q1r2s3", "p0q1r2s3t4u5")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
