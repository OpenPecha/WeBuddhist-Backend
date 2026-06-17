"""merge event image and accumulator user_id heads

Revision ID: 4721283b22a9
Revises: f6666ebb36dc, f8a9b0c1d2e3
Create Date: 2026-06-13 16:53:02.856763

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4721283b22a9'
down_revision: Union[str, None] = ('f6666ebb36dc', 'f8a9b0c1d2e3')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
