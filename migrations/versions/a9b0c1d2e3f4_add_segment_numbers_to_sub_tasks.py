"""add segment_numbers to sub_tasks

Revision ID: a9b0c1d2e3f4
Revises: c8d9e0f1a2b3
Create Date: 2026-07-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "a9b0c1d2e3f4"
down_revision: Union[str, None] = "c8d9e0f1a2b3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "sub_tasks",
        sa.Column(
            "segment_numbers",
            postgresql.ARRAY(sa.Integer()),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("sub_tasks", "segment_numbers")
