"""add_display_order_to_tags

Revision ID: 8674a8b73191
Revises: i1j2k3l4m5n6
Create Date: 2026-06-17 22:20:26.133960

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8674a8b73191'
down_revision: Union[str, None] = 'i1j2k3l4m5n6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
