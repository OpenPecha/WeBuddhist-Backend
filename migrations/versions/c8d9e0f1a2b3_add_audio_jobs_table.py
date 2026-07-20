"""add audio_jobs table for async TTS generation via SQS

Revision ID: c8d9e0f1a2b3
Revises: g2h3i4j5k6l7
Create Date: 2026-07-20 09:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from migrations.idempotency import index_exists, table_exists

revision: str = "c8d9e0f1a2b3"
down_revision: Union[str, None] = "g2h3i4j5k6l7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if not table_exists("audio_jobs"):
        op.create_table(
            "audio_jobs",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
            sa.Column("day_id", sa.UUID(), nullable=True),
            sa.Column("sub_task_id", sa.UUID(), nullable=True),
            sa.Column("language", sa.String(length=16), nullable=False),
            sa.Column("audio_type", sa.String(length=64), nullable=False),
            sa.Column("voice_name", sa.String(length=128), nullable=False),
            sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
            sa.Column("result", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column("error_message", sa.Text(), nullable=True),
            sa.Column("sqs_message_id", sa.String(length=128), nullable=True),
            sa.Column("created_by", sa.String(length=255), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
            sa.ForeignKeyConstraint(["day_id"], ["items.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["sub_task_id"], ["sub_tasks.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )

    if not index_exists("audio_jobs", "idx_audio_jobs_status"):
        op.create_index("idx_audio_jobs_status", "audio_jobs", ["status"], unique=False)

    if not index_exists("audio_jobs", "idx_audio_jobs_day_id"):
        op.create_index("idx_audio_jobs_day_id", "audio_jobs", ["day_id"], unique=False)

    if not index_exists("audio_jobs", "idx_audio_jobs_sub_task_id"):
        op.create_index("idx_audio_jobs_sub_task_id", "audio_jobs", ["sub_task_id"], unique=False)

    if not index_exists("audio_jobs", "idx_audio_jobs_created_at"):
        op.create_index("idx_audio_jobs_created_at", "audio_jobs", ["created_at"], unique=False)


def downgrade() -> None:
    if index_exists("audio_jobs", "idx_audio_jobs_created_at"):
        op.drop_index("idx_audio_jobs_created_at", table_name="audio_jobs")

    if index_exists("audio_jobs", "idx_audio_jobs_sub_task_id"):
        op.drop_index("idx_audio_jobs_sub_task_id", table_name="audio_jobs")

    if index_exists("audio_jobs", "idx_audio_jobs_day_id"):
        op.drop_index("idx_audio_jobs_day_id", table_name="audio_jobs")

    if index_exists("audio_jobs", "idx_audio_jobs_status"):
        op.drop_index("idx_audio_jobs_status", table_name="audio_jobs")

    if table_exists("audio_jobs"):
        op.drop_table("audio_jobs")
