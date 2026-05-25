from sqlalchemy import Column, Integer, DateTime, ForeignKey, Index, UUID, String
from sqlalchemy.orm import relationship
from uuid import uuid4
from pecha_api.db.database import Base
from _datetime import datetime
import _datetime


class SubTaskTimestamp(Base):
    __tablename__ = "sub_task_timestamps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    sub_task_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sub_tasks.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    start_ms = Column(Integer, nullable=False)
    end_ms = Column(Integer, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        default=datetime.now(_datetime.timezone.utc),
        nullable=False,
    )
    created_by = Column(String(255), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.now(_datetime.timezone.utc),
    )
    updated_by = Column(String(255))

    sub_task = relationship("PlanSubTask", back_populates="timestamp")

    __table_args__ = (
        Index("idx_sub_task_timestamps_sub_task_id", "sub_task_id"),
    )
