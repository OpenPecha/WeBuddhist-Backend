"""merge event_chants group_recitation featured and group_posts heads

Revision ID: c0a9470c1ce3
Revises: d9bcc81e67c6, f92e40f4092f, gp4d5e6f7g8h
Create Date: 2026-07-28 11:50:27.453886

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c0a9470c1ce3'
down_revision: Union[str, None] = ('d9bcc81e67c6', 'f92e40f4092f', 'gp4d5e6f7g8h')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
