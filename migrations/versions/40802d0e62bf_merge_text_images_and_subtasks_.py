"""merge text_images and subtasks migrations

Revision ID: 40802d0e62bf
Revises: 64d3723c7834, ba7fbc446df1
Create Date: 2026-02-03 17:39:31.940698

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '40802d0e62bf'
down_revision: Union[str, None] = ('64d3723c7834', 'ba7fbc446df1')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
