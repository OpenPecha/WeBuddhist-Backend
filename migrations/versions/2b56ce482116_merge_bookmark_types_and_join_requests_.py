"""merge bookmark types and join requests heads

Revision ID: 2b56ce482116
Revises: 7dd696782523, bk2b3c4d5e6f
Create Date: 2026-08-21 10:25:39.667241

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2b56ce482116'
down_revision: Union[str, None] = ('7dd696782523', 'bk2b3c4d5e6f')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
