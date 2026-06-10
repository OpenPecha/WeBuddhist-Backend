"""merge_verse_of_day_and_recitation_collection_heads

Revision ID: 0bb142fb9e48
Revises: 4dc71853233a, 503196734168
Create Date: 2026-06-10 14:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0bb142fb9e48"
down_revision: Union[str, Sequence[str], None] = ("4dc71853233a", "503196734168")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
