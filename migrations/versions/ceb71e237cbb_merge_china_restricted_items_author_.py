"""merge china restricted items, author group status, and event timezone heads

Revision ID: ceb71e237cbb
Revises: 4adfb8cfd7e5, ag1b2c3d4e5f, evt2a3b4c5d6f
Create Date: 2026-08-29 13:10:46.013113

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ceb71e237cbb'
down_revision: Union[str, None] = ('4adfb8cfd7e5', 'ag1b2c3d4e5f', 'evt2a3b4c5d6f')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
