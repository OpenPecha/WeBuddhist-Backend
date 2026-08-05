"""add author and user phone authentication fields

Revision ID: b4d7e9f1a2c3
Revises: afc6c3f71329
Create Date: 2026-08-05 12:30:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b4d7e9f1a2c3"
down_revision: Union[str, None] = "afc6c3f71329"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("authors", "email", existing_type=sa.String(length=255), nullable=True)
    op.alter_column("authors", "password", existing_type=sa.String(length=255), nullable=True)
    op.add_column(
        "authors",
        sa.Column("phone_number", sa.String(length=16), nullable=True),
    )
    op.create_index(
        op.f("ix_authors_phone_number"),
        "authors",
        ["phone_number"],
        unique=True,
    )
    op.alter_column("users", "email", existing_type=sa.String(), nullable=True)
    op.add_column(
        "users",
        sa.Column("phone_number", sa.String(length=16), nullable=True),
    )
    op.create_index(
        op.f("ix_users_phone_number"),
        "users",
        ["phone_number"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_users_phone_number"), table_name="users")
    op.drop_column("users", "phone_number")
    op.alter_column("users", "email", existing_type=sa.String(), nullable=False)
    op.drop_index(op.f("ix_authors_phone_number"), table_name="authors")
    op.drop_column("authors", "phone_number")
    op.alter_column("authors", "password", existing_type=sa.String(length=255), nullable=False)
    op.alter_column("authors", "email", existing_type=sa.String(length=255), nullable=False)
