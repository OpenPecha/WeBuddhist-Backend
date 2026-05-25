from sqlalchemy import Column, Integer, DateTime, ForeignKey, BigInteger, Index, UUID, String
from sqlalchemy.orm import relationship
from uuid import uuid4
from pecha_api.db.database import Base
from _datetime import datetime
import _datetime


class PlanItemAudio(Base):
    __tablename__ = "plan_item_audio"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    plan_item_id = Column(
        UUID(as_uuid=True),
        ForeignKey("items.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    audio_key = Column(String(1000), nullable=False)
    duration_ms = Column(Integer, nullable=True)
    mime_type = Column(String(64), nullable=True)
    file_size_bytes = Column(BigInteger, nullable=True)

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

    plan_item = relationship("PlanItem", back_populates="audio")

    __table_args__ = (
        Index("idx_plan_item_audio_plan_item_id", "plan_item_id"),
    )
