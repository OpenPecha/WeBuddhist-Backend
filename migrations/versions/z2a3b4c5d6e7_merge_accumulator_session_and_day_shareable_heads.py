"""merge accumulator session and day shareable heads

Revision ID: z2a3b4c5d6e7
Revises: z0a1b2c3d4e5, z1a2b3c4d5e6
Create Date: 2026-06-26 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "z2a3b4c5d6e7"
down_revision: Union[str, Sequence[str], None] = ("z0a1b2c3d4e5", "z1a2b3c4d5e6")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
