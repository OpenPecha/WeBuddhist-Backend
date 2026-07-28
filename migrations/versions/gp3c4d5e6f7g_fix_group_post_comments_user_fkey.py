"""Fix group_post_comments user_id foreign key to reference authors table

Revision ID: gp3c4d5e6f7g
Revises: gp2b3c4d5e6f
Create Date: 2026-07-27 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'gp3c4d5e6f7g'
down_revision: Union[str, None] = 'gp2b3c4d5e6f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the old foreign key constraint that references users table
    op.drop_constraint('group_post_comments_user_id_fkey', 'group_post_comments', type_='foreignkey')

    # Add new foreign key constraint that references authors table
    # Authors table is where user_id comes from (via JWT token validation)
    op.create_foreign_key(
        'group_post_comments_user_id_fkey',
        'group_post_comments',
        'authors',
        ['user_id'],
        ['id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    # Revert back to original foreign key constraint
    op.drop_constraint('group_post_comments_user_id_fkey', 'group_post_comments', type_='foreignkey')

    op.create_foreign_key(
        'group_post_comments_user_id_fkey',
        'group_post_comments',
        'users',
        ['user_id'],
        ['id'],
        ondelete='CASCADE'
    )
