"""add_event_format_to_events

Revision ID: 6f5785b95f50
Revises: 11527cc6c6c4
Create Date: 2026-09-02 10:38:01.788722

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6f5785b95f50'
down_revision: Union[str, None] = '11527cc6c6c4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('events', sa.Column('event_format', sa.String(length=10), nullable=True))


def downgrade() -> None:
    op.drop_column('events', 'event_format')
