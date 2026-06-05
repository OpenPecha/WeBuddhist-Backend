"""remove EDITOR from author_group_member_role enum

Revision ID: c3d4e5f6a7b8
Revises: f9a0b1c2d3e4
Create Date: 2026-05-21 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, None] = "f9a0b1c2d3e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

NEW_ENUM = "author_group_member_role_new"
OLD_ENUM = "author_group_member_role"


def upgrade() -> None:
    op.execute("UPDATE author_group_members SET role = 'ADMIN' WHERE role = 'EDITOR'")
    op.execute("UPDATE author_group_invites SET role = 'ADMIN' WHERE role = 'EDITOR'")

    op.execute(f"ALTER TYPE {OLD_ENUM} RENAME TO {OLD_ENUM}_old")
    op.execute(
        f"CREATE TYPE {NEW_ENUM} AS ENUM ('OWNER', 'ADMIN', 'AUTHOR', 'VIEWER')"
    )
    op.execute(
        f"""
        ALTER TABLE author_group_members
        ALTER COLUMN role TYPE {NEW_ENUM}
        USING role::text::{NEW_ENUM}
        """
    )
    op.execute(
        f"""
        ALTER TABLE author_group_invites
        ALTER COLUMN role TYPE {NEW_ENUM}
        USING role::text::{NEW_ENUM}
        """
    )
    op.execute(f"ALTER TYPE {NEW_ENUM} RENAME TO {OLD_ENUM}")
    op.execute(f"DROP TYPE {OLD_ENUM}_old")


def downgrade() -> None:
    op.execute(f"ALTER TYPE {OLD_ENUM} RENAME TO {OLD_ENUM}_old")
    op.execute(
        f"CREATE TYPE {NEW_ENUM} AS ENUM ('OWNER', 'ADMIN', 'EDITOR', 'AUTHOR', 'VIEWER')"
    )
    op.execute(
        f"""
        ALTER TABLE author_group_members
        ALTER COLUMN role TYPE {NEW_ENUM}
        USING role::text::{NEW_ENUM}
        """
    )
    op.execute(
        f"""
        ALTER TABLE author_group_invites
        ALTER COLUMN role TYPE {NEW_ENUM}
        USING role::text::{NEW_ENUM}
        """
    )
    op.execute(f"ALTER TYPE {NEW_ENUM} RENAME TO {OLD_ENUM}")
    op.execute(f"DROP TYPE {OLD_ENUM}_old")
