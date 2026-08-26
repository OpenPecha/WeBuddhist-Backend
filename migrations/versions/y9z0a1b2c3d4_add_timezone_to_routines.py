"""add timezone column to routines

Revision ID: y9z0a1b2c3d4
Revises: x8y9z0a1b2c3
Create Date: 2026-06-23 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from migrations.idempotency import column_exists

# revision identifiers, used by Alembic.
revision: str = "y9z0a1b2c3d4"
down_revision: Union[str, None] = "x8y9z0a1b2c3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if not column_exists("routines", "timezone"):
        op.add_column(
            "routines",
            sa.Column("timezone", sa.String(length=64), nullable=True),
        )


def downgrade() -> None:
    if column_exists("routines", "timezone"):
        op.drop_column("routines", "timezone")
