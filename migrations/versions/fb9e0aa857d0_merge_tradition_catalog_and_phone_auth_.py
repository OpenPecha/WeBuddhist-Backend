"""merge tradition catalog and phone auth heads

Revision ID: fb9e0aa857d0
Revises: 6dc5f88f5637, tr1a2b3c4d5e
Create Date: 2026-08-11 08:50:12.622046

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fb9e0aa857d0'
down_revision: Union[str, None] = ('6dc5f88f5637', 'tr1a2b3c4d5e')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
