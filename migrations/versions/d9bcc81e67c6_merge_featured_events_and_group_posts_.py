"""merge featured events and group posts heads

Revision ID: d9bcc81e67c6
Revises: a1b2c3d4e5f0, gp2b3c4d5e6f
Create Date: 2026-07-27 16:04:49.986749

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd9bcc81e67c6'
down_revision: Union[str, None] = ('a1b2c3d4e5f0', 'gp2b3c4d5e6f')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
