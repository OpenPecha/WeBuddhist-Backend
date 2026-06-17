"""add day_notifications table

Revision ID: d9e8f7a6b5c4
Revises: 4721283b22a9
Create Date: 2026-06-13 22:48:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd9e8f7a6b5c4'
down_revision: Union[str, None] = '4721283b22a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the imagetype enum if it doesn't exist
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE imagetype AS ENUM ('PLAN', 'CUSTOM');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Create day_notifications table
    op.create_table(
        'day_notifications',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('day_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('image_url', sa.String(length=1000), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['day_id'], ['items.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('day_id', name='uq_day_notifications_day_id')
    )
    
    # Add image_type column with enum type (enum already exists)
    op.execute("""
        ALTER TABLE day_notifications 
        ADD COLUMN image_type imagetype
    """)
    
    # Create index on day_id for query performance
    op.create_index('idx_day_notifications_day_id', 'day_notifications', ['day_id'], unique=False)


def downgrade() -> None:
    # Drop index
    op.drop_index('idx_day_notifications_day_id', table_name='day_notifications')
    
    # Drop table
    op.drop_table('day_notifications')
    
    # Drop enum type
    op.execute("DROP TYPE imagetype")
