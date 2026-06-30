"""merge_title_and_series_backfill_heads

Revision ID: dfd2dcd179fd
Revises: 07198c5d0b20, 31ed800a4c85
Create Date: 2026-06-30 12:53:01.302873

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dfd2dcd179fd'
down_revision: Union[str, None] = ('07198c5d0b20', '31ed800a4c85')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
