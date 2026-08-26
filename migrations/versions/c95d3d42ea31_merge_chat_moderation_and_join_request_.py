"""merge chat moderation and join request notification heads

Revision ID: c95d3d42ea31
Revises: b7f790529755, ci4d5e6f7a8b
Create Date: 2026-08-24 15:03:15.622960

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c95d3d42ea31'
down_revision: Union[str, None] = ('b7f790529755', 'ci4d5e6f7a8b')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
