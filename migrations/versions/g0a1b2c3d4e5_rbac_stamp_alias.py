"""rbac stamp alias (development deploy compatibility)

Revision ID: g0a1b2c3d4e5
Revises: 440953ec8a21
Create Date: 2026-06-17 07:30:00.000000

Legacy stamp recorded on the development database after RBAC schema changes
were applied. No DDL; reconnects that stamp to the migration graph.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "g0a1b2c3d4e5"
down_revision: Union[str, None] = "440953ec8a21"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
