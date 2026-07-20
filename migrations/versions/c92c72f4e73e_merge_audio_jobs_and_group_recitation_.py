"""merge audio_jobs and group_recitation_collection

Revision ID: c92c72f4e73e
Revises: c8d9e0f1a2b3, h3i4j5k6l7m8
Create Date: 2026-07-20 17:23:50.684385

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c92c72f4e73e'
down_revision: Union[str, None] = ('c8d9e0f1a2b3', 'h3i4j5k6l7m8')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
