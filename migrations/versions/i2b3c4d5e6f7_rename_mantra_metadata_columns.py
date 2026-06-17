"""rename mantra_metadata columns

Rename text -> mantra, meaning -> title, transliteration -> pronunciation.

Revision ID: i2b3c4d5e6f7
Revises: h1a2b3c4d5e6
Create Date: 2026-06-17 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "i2b3c4d5e6f7"
down_revision: Union[str, None] = "h1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("mantra_metadata", "text", new_column_name="mantra")
    op.alter_column("mantra_metadata", "meaning", new_column_name="title")
    op.alter_column("mantra_metadata", "transliteration", new_column_name="pronunciation")


def downgrade() -> None:
    op.alter_column("mantra_metadata", "pronunciation", new_column_name="transliteration")
    op.alter_column("mantra_metadata", "title", new_column_name="meaning")
    op.alter_column("mantra_metadata", "mantra", new_column_name="text")
