"""merge tag_metadata and other heads

Revision ID: i1j2k3l4m5n6
Revises: d9e8f7a6b5c4, j3c4d5e6f7a8
Create Date: 2026-06-17 17:49:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "i1j2k3l4m5n6"
down_revision: Union[str, Sequence[str], None] = ("d9e8f7a6b5c4", "j3c4d5e6f7a8")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
