from sqlalchemy import Column, DateTime, String, ForeignKey, UUID, Index
from sqlalchemy.orm import relationship
from uuid import uuid4
from pecha_api.db.database import Base
from _datetime import datetime
import _datetime


class SubTaskPreset(Base):
    __tablename__ = "preset_table"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    subtask_id = Column(UUID(as_uuid=True), ForeignKey('sub_tasks.id', ondelete='CASCADE'), nullable=False, unique=True)
    version_id = Column(UUID(as_uuid=True), nullable=False)
    language = Column(String(50), nullable=False)

    created_at = Column(DateTime(timezone=True), default=datetime.now(_datetime.timezone.utc), nullable=False)
    created_by = Column(String(255), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.now(_datetime.timezone.utc), onupdate=datetime.now(_datetime.timezone.utc))
    updated_by = Column(String(255))

    sub_task = relationship("PlanSubTask", back_populates="preset")

    __table_args__ = (
        Index("idx_preset_subtask_id", "subtask_id"),
        Index("idx_preset_version_id", "version_id"),
    )
