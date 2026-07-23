"""merge group event participants and group recitation collection session type

Revision ID: 0b7d3f7e1979
Revises: f7a8b9c0d1e2, 8ddff2b6a149
Create Date: 2026-07-23 15:28:48.853940

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0b7d3f7e1979'
down_revision: Union[str, None] = ('f7a8b9c0d1e2', '8ddff2b6a149')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
