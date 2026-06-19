"""merge task youtube videos head

Revision ID: 84db00227eef
Revises: 44ef04b271d1, q1r2s3t4u5v6
Create Date: 2026-06-19 13:02:01.238356

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '84db00227eef'
down_revision: Union[str, None] = ('44ef04b271d1', 'q1r2s3t4u5v6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
