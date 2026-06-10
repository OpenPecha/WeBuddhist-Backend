"""merge_migration_heads

Revision ID: 9fad9b63fa9a
Revises: 4dc71853233a, 503196734168
Create Date: 2026-06-10 10:46:01.542208

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9fad9b63fa9a'
down_revision: Union[str, None] = ('4dc71853233a', '503196734168')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
