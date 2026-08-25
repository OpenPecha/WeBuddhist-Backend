"""merge event notification and join request heads

Revision ID: 813cecbdd710
Revises: c95d3d42ea31, ev1a2b3c4d5e
Create Date: 2026-08-25 08:42:17.406731

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '813cecbdd710'
down_revision: Union[str, None] = ('c95d3d42ea31', 'ev1a2b3c4d5e')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
