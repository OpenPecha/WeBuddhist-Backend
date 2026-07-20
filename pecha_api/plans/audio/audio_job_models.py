from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text, UUID
from sqlalchemy.dialects.postgresql import JSONB

from pecha_api.db.database import Base
from pecha_api.plans.plans_enums import AudioJobStatus


class AudioJob(Base):
    __tablename__ = "audio_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    status = Column(String(32), nullable=False, default=AudioJobStatus.PENDING.value)
    day_id = Column(UUID(as_uuid=True), ForeignKey("items.id", ondelete="SET NULL"), nullable=True)
    sub_task_id = Column(UUID(as_uuid=True), ForeignKey("sub_tasks.id", ondelete="SET NULL"), nullable=True)
    language = Column(String(16), nullable=False)
    audio_type = Column(String(64), nullable=False)
    voice_name = Column(String(128), nullable=False)
    payload = Column(JSONB, nullable=False, default=dict)
    result = Column(JSONB, nullable=True)
    error_message = Column(Text, nullable=True)
    sqs_message_id = Column(String(128), nullable=True)
    created_by = Column(String(255), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    attempt_count = Column(Integer, nullable=False, default=0, server_default="0")

    __table_args__ = (
        Index("idx_audio_jobs_status", "status"),
        Index("idx_audio_jobs_day_id", "day_id"),
        Index("idx_audio_jobs_sub_task_id", "sub_task_id"),
        Index("idx_audio_jobs_created_at", "created_at"),
    )
