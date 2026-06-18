"""merge_develop_migrations

Revision ID: 888b759bcd6a
Revises: e2b6a3bdc52b, k4d5e6f7a8b9
Create Date: 2026-06-18 11:14:39.838985

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '888b759bcd6a'
down_revision: Union[str, None] = ('e2b6a3bdc52b', 'k4d5e6f7a8b9')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
