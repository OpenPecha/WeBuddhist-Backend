"""make accumulator user_id nullable

Preset accumulators are not owned by a user (they belong to a group), so
user_id must be allowed to be NULL. User-created accumulators continue to set
user_id from the authenticated user.

Revision ID: f6666ebb36dc
Revises: 549f04829736
Create Date: 2026-06-13 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f6666ebb36dc'
down_revision: Union[str, None] = '549f04829736'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('accumulators', 'user_id', existing_type=sa.UUID(), nullable=True)


def downgrade() -> None:
    op.alter_column('accumulators', 'user_id', existing_type=sa.UUID(), nullable=False)
