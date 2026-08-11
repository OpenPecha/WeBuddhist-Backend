"""merge_user_metadata_and_likes_heads

Revision ID: 98fc8b142c69
Revises: afc6c3f71329, um1a2b3c4d5e
Create Date: 2026-08-10 16:24:08.543700

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '98fc8b142c69'
down_revision: Union[str, None] = ('afc6c3f71329', 'um1a2b3c4d5e')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
