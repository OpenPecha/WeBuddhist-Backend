"""merge_group_accumulator_soft_delete_and_plan_videos

Revision ID: 2da1ef4d53a3
Revises: 3f8e9d2c1b0a, a6b7c8d9e0f1
Create Date: 2026-06-29 22:46:43.038042

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2da1ef4d53a3'
down_revision: Union[str, None] = ('3f8e9d2c1b0a', 'a6b7c8d9e0f1')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
