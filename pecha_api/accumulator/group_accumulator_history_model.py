from sqlalchemy import Column, DateTime, UUID, Integer, ForeignKey, Index
from sqlalchemy.orm import relationship
from ..db.database import Base
from uuid import uuid4
import _datetime
from _datetime import datetime


class GroupAccumulatorHistory(Base):
    __tablename__ = "group_accumulator_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    group_accumulator_id = Column(UUID(as_uuid=True), ForeignKey("group_accumulators.id", ondelete="CASCADE"), nullable=False)
    user_group_accumulator_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user_group_accumulators.id", ondelete="SET NULL"),
        nullable=True,
    )
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    count = Column(Integer, nullable=False)

    user_group_accumulator = relationship(
        "UserGroupAccumulator",
        back_populates="history_rows",
    )

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(_datetime.timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(_datetime.timezone.utc), onupdate=lambda: datetime.now(_datetime.timezone.utc))

    __table_args__ = (
        Index("idx_group_accumulator_history_group_accumulator_id", "group_accumulator_id"),
        Index("idx_group_accumulator_history_user_id", "user_id"),
    )
