"""merge chant completion and chat system heads

Revision ID: 4b87b7a7d6c1
Revises: 56730dda7b5f, d537d7dae9ad
Create Date: 2026-07-30 10:52:03.658897

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4b87b7a7d6c1'
down_revision: Union[str, None] = ('56730dda7b5f', 'd537d7dae9ad')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
