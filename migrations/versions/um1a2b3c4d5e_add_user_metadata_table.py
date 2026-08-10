"""add_user_metadata_table

Revision ID: um1a2b3c4d5e
Revises: gp5e6f7g8h9i
Create Date: 2026-08-10 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'um1a2b3c4d5e'
down_revision: Union[str, None] = 'gp5e6f7g8h9i'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Use existing languagecode enum type
    languagecode_enum = postgresql.ENUM('EN', 'BO', 'ZH', 'HI', 'NE', 'MN', 'LA', name='languagecode', create_type=False)
    
    op.create_table(
        'user_metadata',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('language', languagecode_enum, nullable=False, server_default='EN'),
        sa.Column('timezone', sa.String(length=64), nullable=False, server_default='Asia/Kathmandu'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', name='uq_user_metadata_user_id'),
    )
    op.create_index('idx_user_metadata_user_id', 'user_metadata', ['user_id'], unique=True)


def downgrade() -> None:
    op.drop_index('idx_user_metadata_user_id', table_name='user_metadata')
    op.drop_table('user_metadata')
