"""add has_seen_onboarding to users

Revision ID: z3a4b5c6d7e8
Revises: z2a3b4c5d6e7
Create Date: 2026-06-27 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from migrations.idempotency import column_exists


revision: str = "z3a4b5c6d7e8"
down_revision: Union[str, None] = "z2a3b4c5d6e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if not column_exists("users", "has_seen_onboarding"):
        op.add_column(
            "users",
            sa.Column(
                "has_seen_onboarding",
                sa.Boolean(),
                server_default="FALSE",
                nullable=False,
            ),
        )


def downgrade() -> None:
    if column_exists("users", "has_seen_onboarding"):
        op.drop_column("users", "has_seen_onboarding")
