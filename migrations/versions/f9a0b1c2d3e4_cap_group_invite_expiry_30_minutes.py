"""cap group invite expires_at to 30 minutes from created_at

Revision ID: f9a0b1c2d3e4
Revises: e7f8a9b0c1d2
Create Date: 2026-05-20 18:00:00.000000

Legacy invites stored expires_at ~30 days ahead (client-supplied or days-based TTL).
New invites use server-side GROUP_INVITE_EXPIRY_MINUTES (default 30).
"""
from typing import Sequence, Union

from alembic import op

revision: str = "f9a0b1c2d3e4"
down_revision: Union[str, None] = "e7f8a9b0c1d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE author_group_invites
        SET expires_at = created_at + INTERVAL '30 minutes'
        WHERE status = 'PENDING'
          AND expires_at > created_at + INTERVAL '30 minutes'
        """
    )


def downgrade() -> None:
    pass
