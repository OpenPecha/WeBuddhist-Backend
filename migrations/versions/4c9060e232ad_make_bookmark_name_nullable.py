"""make_bookmark_name_nullable

Revision ID: 4c9060e232ad
Revises: 9913dcde55ca
Create Date: 2026-06-10 11:56:52.978590

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4c9060e232ad'
down_revision: Union[str, None] = '9913dcde55ca'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('bookmarks', 'name',
                    existing_type=sa.String(255),
                    nullable=True)


def downgrade() -> None:
    op.alter_column('bookmarks', 'name',
                    existing_type=sa.String(255),
                    nullable=False)
