"""add_tag_segments_table

Revision ID: e2b6a3bdc52b
Revises: 8674a8b73191
Create Date: 2026-06-17 22:22:28.330376

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e2b6a3bdc52b'
down_revision: Union[str, None] = '8674a8b73191'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
