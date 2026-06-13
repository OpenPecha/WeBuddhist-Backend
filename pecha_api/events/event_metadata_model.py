from uuid import uuid4

from sqlalchemy import Column, String, Text, UUID, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship

from pecha_api.db.database import Base
from pecha_api.plans.plans_enums import LanguageCodeEnum


class EventMetadata(Base):
    __tablename__ = "event_metadata"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    event_id = Column(
        UUID(as_uuid=True),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
    )
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    language = Column(LanguageCodeEnum, nullable=False)

    event = relationship("Event", back_populates="metadata_entries")

    __table_args__ = (
        UniqueConstraint("event_id", "language", name="uq_event_metadata_event_language"),
        Index("idx_event_metadata_event_language", "event_id", "language"),
    )
