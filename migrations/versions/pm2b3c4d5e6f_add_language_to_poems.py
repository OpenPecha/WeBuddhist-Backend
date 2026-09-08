"""add_language_to_poems

Revision ID: pm2b3c4d5e6f
Revises: pm1a2b3c4d5e
Create Date: 2026-08-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'pm2b3c4d5e6f'
down_revision: Union[str, None] = 'pm1a2b3c4d5e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


LANGUAGECODE_VALUES = ("EN", "BO", "ZH", "HI", "NE", "MN", "LA")


def upgrade() -> None:
    op.add_column(
        "poems",
        sa.Column(
            "language",
            postgresql.ENUM(*LANGUAGECODE_VALUES, name="languagecode", create_type=False),
            nullable=True,
        ),
    )
    op.execute("UPDATE poems SET language = 'EN'")
    op.alter_column("poems", "language", nullable=False, server_default="EN")

    op.create_index(
        "idx_poems_language",
        "poems",
        ["language"],
        unique=False,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("idx_poems_language", table_name="poems")
    op.drop_column("poems", "language")
