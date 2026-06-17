"""merge verse_metadata and accumulator_mantra_fk heads

Revision ID: 549f04829736
Revises: d1e2f3a4b5c6, e6f7a8b9c0d1
Create Date: 2026-06-13 16:06:38.498457

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '549f04829736'
down_revision: Union[str, None] = ('d1e2f3a4b5c6', 'e6f7a8b9c0d1')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
