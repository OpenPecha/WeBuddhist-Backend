"""merge featured tags and author groups heads

Revision ID: ecccb9c7779b
Revises: 9f3b6c1d2e7a, d1f3a9c2b7e4
Create Date: 2026-05-28 16:04:29.741663

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ecccb9c7779b'
down_revision: Union[str, None] = ('9f3b6c1d2e7a', 'd1f3a9c2b7e4')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
