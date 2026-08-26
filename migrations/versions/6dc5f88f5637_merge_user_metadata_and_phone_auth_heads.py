"""merge_user_metadata_and_phone_auth_heads

Revision ID: 6dc5f88f5637
Revises: 98fc8b142c69, b4d7e9f1a2c3
Create Date: 2026-08-10 17:00:45.228764

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6dc5f88f5637'
down_revision: Union[str, None] = ('98fc8b142c69', 'b4d7e9f1a2c3')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
