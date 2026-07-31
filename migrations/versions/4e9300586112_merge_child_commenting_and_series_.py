"""merge child commenting and series partner soft delete heads

Revision ID: 4e9300586112
Revises: f2a3b4c5d6e8, p3q4r5s6t7u8
Create Date: 2026-07-31 11:21:42.697928

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4e9300586112'
down_revision: Union[str, None] = ('f2a3b4c5d6e8', 'p3q4r5s6t7u8')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
