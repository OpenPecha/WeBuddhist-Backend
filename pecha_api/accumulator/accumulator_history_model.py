from sqlalchemy import Column, DateTime, UUID, Integer, ForeignKey, Index
from ..db.database import Base
from uuid import uuid4
import _datetime
from _datetime import datetime


class AccumulatorHistory(Base):
    __tablename__ = "accumulator_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    accumulator_id = Column(UUID(as_uuid=True), ForeignKey("accumulators.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    count = Column(Integer, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(_datetime.timezone.utc), nullable=False)

    __table_args__ = (
        Index("idx_accumulator_history_accumulator_id", "accumulator_id"),
        Index("idx_accumulator_history_user_id", "user_id"),
    )
