from sqlalchemy import Column, Integer, DateTime, ForeignKey, Index, UUID, String
from sqlalchemy.orm import relationship
from uuid import uuid4
from ...db.database import Base
from _datetime import datetime
import _datetime


class PlanItem(Base):
    __tablename__ = "items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    plan_id = Column(UUID(as_uuid=True), ForeignKey('plans.id', ondelete='CASCADE'), nullable=False)
    day_number = Column(Integer, nullable=False)

    created_at = Column(DateTime(timezone=True), default=datetime.now(_datetime.timezone.utc),nullable=False)
    created_by = Column(String(255), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.now(_datetime.timezone.utc))
    updated_by = Column(String(255))

    audio = relationship(
        "PlanItemAudio",
        back_populates="plan_item",
        uselist=False,
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_plan_items_plan_day", "plan_id", "day_number"),
    )


from pecha_api.plans.audio.plan_item_audio_models import PlanItemAudio  # noqa: F401, E402

