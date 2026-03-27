"""merge migration heads

Revision ID: e56f9b50e5f2
Revises: 0dfe34c1c026, a7b8c9d0e1f2
Create Date: 2026-03-23 14:13:32.683572

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e56f9b50e5f2'
down_revision: Union[str, None] = ('0dfe34c1c026', 'a7b8c9d0e1f2')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
