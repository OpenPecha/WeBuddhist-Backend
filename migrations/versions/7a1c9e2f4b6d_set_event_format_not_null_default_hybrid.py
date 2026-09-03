"""set_event_format_not_null_default_hybrid

Revision ID: 7a1c9e2f4b6d
Revises: b9dd872a530c
Create Date: 2026-09-03 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7a1c9e2f4b6d'
down_revision: Union[str, None] = 'b9dd872a530c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Backfill existing NULLs before enforcing NOT NULL
    op.execute("UPDATE events SET event_format = 'hybrid' WHERE event_format IS NULL")
    op.alter_column(
        'events', 'event_format',
        existing_type=sa.String(length=10),
        nullable=False,
        server_default='hybrid',
    )


def downgrade() -> None:
    op.alter_column(
        'events', 'event_format',
        existing_type=sa.String(length=10),
        nullable=True,
        server_default=None,
    )
