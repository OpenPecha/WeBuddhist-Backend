"""merge youtube and preset heads

Revision ID: p0q1r2s3t4u5
Revises: n7o8p9q0r1s2, 514802a65782
Create Date: 2026-06-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "p0q1r2s3t4u5"
down_revision: Union[str, Sequence[str], None] = ("n7o8p9q0r1s2", "514802a65782")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
