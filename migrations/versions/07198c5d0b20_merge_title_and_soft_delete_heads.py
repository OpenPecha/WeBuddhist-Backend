"""merge_title_and_soft_delete_heads

Revision ID: 07198c5d0b20
Revises: 2da1ef4d53a3, a1b2c3d4e5f9
Create Date: 2026-06-30 12:09:38.749150

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '07198c5d0b20'
down_revision: Union[str, None] = ('2da1ef4d53a3', 'a1b2c3d4e5f9')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
