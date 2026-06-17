"""add_mantra_table

Revision ID: b7c8d9e0f1a2
Revises: c2d3e4f5a6b7
Create Date: 2026-06-12 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'b7c8d9e0f1a2'
down_revision: Union[str, None] = 'c2d3e4f5a6b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('mantra',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('audio_url', sa.String(length=1000), nullable=True),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('meaning', sa.Text(), nullable=True),
        sa.Column('language', postgresql.ENUM('EN', 'BO', 'ZH', name='languagecode', create_type=False), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('mantra')
