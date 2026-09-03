"""merge event format and develop heads

Revision ID: a8b9c0d1e2f3
Revises: 6f5785b95f50, ceb71e237cbb
Create Date: 2026-09-03 10:48:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a8b9c0d1e2f3"
down_revision: Union[str, None] = ("6f5785b95f50", "ceb71e237cbb")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
