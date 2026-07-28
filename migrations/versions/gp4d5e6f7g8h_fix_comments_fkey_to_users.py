"""Fix group_post_comments foreign key to reference users table

Revision ID: gp4d5e6f7g8h
Revises: gp3c4d5e6f7g
Create Date: 2026-07-27 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'gp4d5e6f7g8h'
down_revision: Union[str, None] = 'gp3c4d5e6f7g'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the foreign key constraint that references authors table
    op.drop_constraint('group_post_comments_user_id_fkey', 'group_post_comments', type_='foreignkey')

    # Add foreign key constraint that references users table (correct)
    op.create_foreign_key(
        'group_post_comments_user_id_fkey',
        'group_post_comments',
        'users',
        ['user_id'],
        ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    # Revert back to authors table reference
    op.drop_constraint('group_post_comments_user_id_fkey', 'group_post_comments', type_='foreignkey')

    op.create_foreign_key(
        'group_post_comments_user_id_fkey',
        'group_post_comments',
        'authors',
        ['user_id'],
        ['id'],
        ondelete='CASCADE'
    )
