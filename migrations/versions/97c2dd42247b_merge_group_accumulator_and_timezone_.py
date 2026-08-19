"""merge group_accumulator and timezone heads

Revision ID: 97c2dd42247b
Revises: y9z0a1b2c3d4, z2b3c4d5e6f7
Create Date: 2026-06-26 16:39:13.147445

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '97c2dd42247b'
down_revision: Union[str, None] = ('y9z0a1b2c3d4', 'z2b3c4d5e6f7')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
