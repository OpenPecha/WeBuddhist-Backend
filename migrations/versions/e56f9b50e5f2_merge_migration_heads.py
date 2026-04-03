"""merge migration heads

Revision ID: e56f9b50e5f2
Revises: 9984d31f026b
Create Date: 2025-04-03 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e56f9b50e5f2'
down_revision: Union[str, None] = '9984d31f026b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # This is a placeholder migration to fix broken migration chain
    pass


def downgrade() -> None:
    pass
