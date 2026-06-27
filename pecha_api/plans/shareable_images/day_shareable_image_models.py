from sqlalchemy import Column, DateTime, ForeignKey, Index, UUID, String
from sqlalchemy.orm import relationship
from uuid import uuid4
from pecha_api.db.database import Base
from _datetime import datetime
import _datetime


class DayShareableImage(Base):
    __tablename__ = "day_shareable_images"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    plan_item_id = Column(
        UUID(as_uuid=True),
        ForeignKey("items.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    thumbnail_key = Column(String(1000), nullable=True)
    shareable_image_key = Column(String(1000), nullable=True)

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

    plan_item = relationship("PlanItem", back_populates="shareable_images")

    __table_args__ = (
        Index("idx_day_shareable_images_plan_item_id", "plan_item_id"),
    )
