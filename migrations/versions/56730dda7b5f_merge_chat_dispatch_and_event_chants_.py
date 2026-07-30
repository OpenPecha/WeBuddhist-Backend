"""merge chat_dispatch and event_chants heads

Revision ID: 56730dda7b5f
Revises: ch2b3c4d5e6f, c0a9470c1ce3
Create Date: 2026-07-29 06:49:54.835115

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '56730dda7b5f'
down_revision: Union[str, None] = ('ch2b3c4d5e6f', 'c0a9470c1ce3')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
