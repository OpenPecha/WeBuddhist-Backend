from _datetime import datetime
import _datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text, UUID
from sqlalchemy.orm import relationship
from uuid import uuid4

from pecha_api.db.database import Base


class PlanVideo(Base):
    __tablename__ = "plan_videos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    plan_id = Column(
        UUID(as_uuid=True),
        ForeignKey("plans.id", ondelete="CASCADE"),
        nullable=False,
    )
    url = Column(Text, nullable=False)
    video_id = Column(String(64), nullable=True)
    title = Column(String(500), nullable=True)
    display_order = Column(Integer, nullable=False, default=0)

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

    plan = relationship("Plan", back_populates="videos")

    __table_args__ = (
        Index("idx_plan_videos_plan_id", "plan_id"),
    )
