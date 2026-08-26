"""merge mala_image and migration-update heads

Revision ID: ffca36f72f3f
Revises: 2d3e4f5a6b7c, d9e8f7a6b5c4
Create Date: 2026-06-17 18:16:01.559417

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ffca36f72f3f'
down_revision: Union[str, None] = ('2d3e4f5a6b7c', 'd9e8f7a6b5c4')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
