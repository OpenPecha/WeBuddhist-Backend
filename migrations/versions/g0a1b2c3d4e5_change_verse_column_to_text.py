"""change verse_metadata verse column from JSONB to Text

Revision ID: g0a1b2c3d4e5
Revises: f9b0c1d2e3f4
Create Date: 2026-06-17 10:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "g0a1b2c3d4e5"
down_revision: Union[str, None] = "f9b0c1d2e3f4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Convert JSONB to Text, stripping quotes from existing JSON string values
    op.execute("""
        ALTER TABLE verse_metadata 
        ALTER COLUMN verse TYPE TEXT 
        USING CASE 
            WHEN jsonb_typeof(verse) = 'string' THEN verse #>> '{}'
            ELSE verse::text
        END
    """)


def downgrade() -> None:
    # Convert Text back to JSONB
    op.execute("""
        ALTER TABLE verse_metadata 
        ALTER COLUMN verse TYPE JSONB 
        USING to_jsonb(verse)
    """)
