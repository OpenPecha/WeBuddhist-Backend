"""merge_likes_and_locations_heads

Revision ID: afc6c3f71329
Revises: b7c4e2a91d33, gp5e6f7g8h9i
Create Date: 2026-08-03 16:03:56.991429

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'afc6c3f71329'
down_revision: Union[str, None] = ('b7c4e2a91d33', 'gp5e6f7g8h9i')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
