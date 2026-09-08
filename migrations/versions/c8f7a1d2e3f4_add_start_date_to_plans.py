"""add start_date to plans

Revision ID: c8f7a1d2e3f4
Revises: e56f9b50e5f2
Create Date: 2026-04-08

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c8f7a1d2e3f4"
down_revision: Union[str, None] = "e56f9b50e5f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    from sqlalchemy import inspect
    
    bind = op.get_bind()
    inspector = inspect(bind)
    
    # Add start_date column only if it doesn't exist
    plans_columns = {col['name'] for col in inspector.get_columns('plans')}
    if 'start_date' not in plans_columns:
        op.add_column(
            "plans",
            sa.Column("start_date", sa.DateTime(timezone=True), nullable=True),
        )


def downgrade() -> None:
    op.drop_column("plans", "start_date")
