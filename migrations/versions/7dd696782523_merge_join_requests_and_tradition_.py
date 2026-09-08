"""merge join requests and tradition catalog heads

Revision ID: 7dd696782523
Revises: 5274a7c4c41a, fb9e0aa857d0
Create Date: 2026-08-19 11:07:29.041847

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7dd696782523'
down_revision: Union[str, None] = ('5274a7c4c41a', 'fb9e0aa857d0')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
