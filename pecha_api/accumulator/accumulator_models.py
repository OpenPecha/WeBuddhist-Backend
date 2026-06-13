from sqlalchemy import Column, String, DateTime, UUID, Text, Index, Integer, ForeignKey
from ..db.database import Base
from uuid import uuid4
import _datetime
from _datetime import datetime
from .accumulator_enums import AccumulatorTypeEnum


class Accumulator(Base):
    __tablename__ = "accumulators"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    group_id = Column(UUID(as_uuid=True), nullable=True)
    type = Column(AccumulatorTypeEnum, nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    target_count = Column(Integer, nullable=True)
    current_count = Column(Integer, nullable=False, default=0)
    text_id = Column(UUID(as_uuid=True), nullable=True)
    mantra_id = Column(
        UUID(as_uuid=True),
        ForeignKey("mantra.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(_datetime.timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(_datetime.timezone.utc), onupdate=lambda: datetime.now(_datetime.timezone.utc))

    __table_args__ = (
        Index("idx_accumulators_user_id", "user_id"),
        Index("idx_accumulators_type", "type"),
    )
