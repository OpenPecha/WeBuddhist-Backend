"""merge event_links branch with develop group recitation collection

Revision ID: 6f9d6b6333d5
Revises: 0b7d3f7e1979, c289b7fe3423
Create Date: 2026-07-23 16:22:37.337832

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6f9d6b6333d5'
down_revision: Union[str, None] = ('0b7d3f7e1979', 'c289b7fe3423')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
