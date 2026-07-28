from sqlalchemy import Column, String, DateTime, UUID, ForeignKey, Index, Boolean
from sqlalchemy.orm import relationship
from ..db.database import Base
from uuid import uuid4
import _datetime
from _datetime import datetime


class Event(Base):
    __tablename__ = "events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    plan_id = Column(UUID(as_uuid=True), ForeignKey("plans.id", ondelete="SET NULL"), nullable=True)
    accumulator_id = Column(UUID(as_uuid=True), ForeignKey("accumulators.id", ondelete="SET NULL"), nullable=True)
    mantra_id = Column(UUID(as_uuid=True), ForeignKey("mantra.id", ondelete="SET NULL"), nullable=True)
    timer_id = Column(UUID(as_uuid=True), ForeignKey("timers.id", ondelete="SET NULL"), nullable=True)
    group_recitation_collection_id = Column(
        UUID(as_uuid=True),
        ForeignKey("group_recitation_collections.id", ondelete="SET NULL"),
        nullable=True,
    )
    group_id = Column(UUID(as_uuid=True), ForeignKey("author_groups.id", ondelete="RESTRICT"), nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    image_url = Column(String(1000), nullable=True)
    featured = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), default=datetime.now(_datetime.timezone.utc), nullable=False)
    created_by = Column(String(255), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.now(_datetime.timezone.utc))

    metadata_entries = relationship(
        "EventMetadata",
        back_populates="event",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    links = relationship(
        "EventLink",
        back_populates="event",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    participants = relationship(
        "GroupEventParticipant",
        back_populates="event",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        Index("idx_events_group_id", "group_id"),
        Index("idx_events_start_date", "start_date"),
        Index("idx_events_end_date", "end_date"),
        Index("idx_events_group_recitation_collection_id", "group_recitation_collection_id"),
        Index("idx_events_featured", "featured"),
    )
