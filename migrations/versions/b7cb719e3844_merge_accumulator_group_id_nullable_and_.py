"""merge accumulator group_id nullable and events heads

Revision ID: b7cb719e3844
Revises: b4c5d6e7f8a0, 68055a51de95
Create Date: 2026-06-13 12:51:02.009187

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7cb719e3844'
down_revision: Union[str, None] = ('b4c5d6e7f8a0', '68055a51de95')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
