"""merge series partner and onboarding heads

Revision ID: 64e5528d818f
Revises: a967e8ec07c8, z3a4b5c6d7e8
Create Date: 2026-06-27 15:26:28.400297

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '64e5528d818f'
down_revision: Union[str, None] = ('a967e8ec07c8', 'z3a4b5c6d7e8')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
