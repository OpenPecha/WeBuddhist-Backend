"""merge_verse_of_day_and_subtitle_heads

Revision ID: 4dc71853233a
Revises: b2c3d4e5f6a8, e8f9a0b1c2d3
Create Date: 2026-06-05 23:18:23.952080

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4dc71853233a'
down_revision: Union[str, None] = ('b2c3d4e5f6a8', 'e8f9a0b1c2d3')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
