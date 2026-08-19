"""merge event_links and group_event_participants

Revision ID: c289b7fe3423
Revises: 8ddff2b6a149, c1d2e3f4a5b7
Create Date: 2026-07-23 12:40:34.953489

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c289b7fe3423'
down_revision: Union[str, None] = ('8ddff2b6a149', 'c1d2e3f4a5b7')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
