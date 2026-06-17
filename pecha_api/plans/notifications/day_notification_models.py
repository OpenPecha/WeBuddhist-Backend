from sqlalchemy import Column, String, Text, DateTime, ForeignKey, UUID, Enum as SQLEnum
from sqlalchemy.orm import relationship
from uuid import uuid4
from ...db.database import Base
from _datetime import datetime
import _datetime
import enum


class ImageTypeEnum(str, enum.Enum):
    PLAN = "PLAN"
    CUSTOM = "CUSTOM"


class DayNotification(Base):
    __tablename__ = "day_notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    day_id = Column(UUID(as_uuid=True), ForeignKey('items.id', ondelete='CASCADE'), nullable=False, unique=True)
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    image_type = Column(SQLEnum(ImageTypeEnum, name='imagetype', create_type=False), nullable=True)
    image_url = Column(String(1000), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=datetime.now(_datetime.timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=True)

    plan_item = relationship("PlanItem", back_populates="notification")
