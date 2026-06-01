from uuid import uuid4
import _datetime
from _datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, String, Text, UUID

from pecha_api.db.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    recipient_author_id = Column(
        UUID(as_uuid=True),
        ForeignKey("authors.id", ondelete="CASCADE"),
        nullable=False,
    )
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=False)
    reference_type = Column(String(100), nullable=True)
    reference_id = Column(UUID(as_uuid=True), nullable=True)
    is_read = Column(Boolean, nullable=False, default=False)
    read_at = Column(DateTime(timezone=True), nullable=True)
    action_1_label = Column(String(100), nullable=True)
    action_1_method = Column(String(10), nullable=True)
    action_1_path = Column(String(500), nullable=True)
    action_2_label = Column(String(100), nullable=True)
    action_2_method = Column(String(10), nullable=True)
    action_2_path = Column(String(500), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=datetime.now(_datetime.timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        Index("idx_notifications_recipient_read", "recipient_author_id", "is_read"),
        Index("idx_notifications_reference", "reference_type", "reference_id"),
    )
