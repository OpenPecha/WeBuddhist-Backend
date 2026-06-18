"""add tag_metadata table and migrate data from tags

Revision ID: k4l5m6n7o8p9
Revises: j3c4d5e6f7a8
Create Date: 2026-06-18 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "k4l5m6n7o8p9"
down_revision: Union[str, None] = "j3c4d5e6f7a8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the languagecode enum type if it doesn't exist
    # (it should already exist from plans table, but check to be safe)
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'languagecode') THEN
                CREATE TYPE languagecode AS ENUM ('EN', 'BO', 'ZH', 'HI', 'NE', 'MN');
            END IF;
        END $$;
    """)

    # Create tag_metadata table
    op.create_table(
        "tag_metadata",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tag_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "language",
            postgresql.ENUM("EN", "BO", "ZH", "HI", "NE", "MN", name="languagecode", create_type=False),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create unique constraint and index
    op.create_unique_constraint(
        "uq_tag_metadata_tag_language",
        "tag_metadata",
        ["tag_id", "language"],
    )
    op.create_index(
        "idx_tag_metadata_tag_language",
        "tag_metadata",
        ["tag_id", "language"],
    )

    # Migrate existing data from tags to tag_metadata
    # Each existing tag gets an EN metadata entry
    op.execute("""
        INSERT INTO tag_metadata (id, tag_id, name, description, language)
        SELECT 
            gen_random_uuid(),
            id,
            name,
            description,
            'EN'::languagecode
        FROM tags
        WHERE name IS NOT NULL AND deleted_at IS NULL
    """)

    # Drop the old unique index on tags.name
    op.execute("""
        DROP INDEX IF EXISTS idx_tags_name_unique
    """)

    # Drop name and description columns from tags table
    op.drop_column("tags", "name")
    op.drop_column("tags", "description")


def downgrade() -> None:
    # Add back name and description columns to tags
    op.add_column(
        "tags",
        sa.Column("name", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "tags",
        sa.Column("description", sa.Text(), nullable=True),
    )

    # Migrate data back from tag_metadata to tags (use EN entries)
    op.execute("""
        UPDATE tags t
        SET 
            name = tm.name,
            description = tm.description
        FROM tag_metadata tm
        WHERE tm.tag_id = t.id AND tm.language = 'EN'
    """)

    # Make name NOT NULL after data migration
    op.alter_column("tags", "name", nullable=False)

    # Recreate the unique index on tags.name
    op.create_index(
        "idx_tags_name_unique",
        "tags",
        ["name"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # Drop tag_metadata table
    op.drop_index("idx_tag_metadata_tag_language", table_name="tag_metadata")
    op.drop_constraint("uq_tag_metadata_tag_language", "tag_metadata", type_="unique")
    op.drop_table("tag_metadata")
