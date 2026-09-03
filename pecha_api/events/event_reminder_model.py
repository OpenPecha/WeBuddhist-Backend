from sqlalchemy import Column, String, DateTime, UUID, ForeignKey, Index, UniqueConstraint, text
from ..db.database import Base
from uuid import uuid4
import _datetime
from _datetime import datetime


class EventReminder(Base):
    __tablename__ = "event_reminders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    event_id = Column(
        UUID(as_uuid=True),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
    )
    reminder_type = Column(String(20), nullable=False)
    fire_at = Column(DateTime(timezone=True), nullable=False)
    sqs_message_id = Column(String(128), nullable=True)
    dispatched_at = Column(DateTime(timezone=True), nullable=True)
    canceled_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now(_datetime.timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("event_id", "reminder_type", name="uq_event_reminders_event_type"),
        Index("idx_event_reminders_event_id", "event_id"),
        Index(
            "idx_event_reminders_due",
            "fire_at",
            postgresql_where=text("dispatched_at IS NULL AND canceled_at IS NULL"),
        ),
    )
