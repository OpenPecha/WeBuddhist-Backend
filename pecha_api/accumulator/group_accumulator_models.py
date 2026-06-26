from sqlalchemy import Column, DateTime, UUID, Integer, ForeignKey, Index
from sqlalchemy.orm import relationship
from ..db.database import Base
from uuid import uuid4
import _datetime
from _datetime import datetime


class GroupAccumulator(Base):
    __tablename__ = "group_accumulators"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    mantra_id = Column(
        UUID(as_uuid=True),
        ForeignKey("mantra.id", ondelete="SET NULL"),
        nullable=True,
    )
    group_id = Column(
        UUID(as_uuid=True),
        ForeignKey("author_groups.id", ondelete="CASCADE"),
        nullable=False,
    )
    target_count = Column(Integer, nullable=True)
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(_datetime.timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(_datetime.timezone.utc), onupdate=lambda: datetime.now(_datetime.timezone.utc))

    mantra = relationship("Mantra")

    __table_args__ = (
        Index("idx_group_accumulators_group_id", "group_id"),
        Index("idx_group_accumulators_mantra_id", "mantra_id"),
    )
