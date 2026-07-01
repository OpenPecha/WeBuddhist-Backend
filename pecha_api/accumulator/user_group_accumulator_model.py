from sqlalchemy import Column, DateTime, UUID, ForeignKey, Index
from sqlalchemy.orm import relationship
from ..db.database import Base
from uuid import uuid4
import _datetime
from _datetime import datetime


class UserGroupAccumulator(Base):
    """A user's participation session in a group accumulator.

    Soft-deleting a row resets the user's active progress while preserving
    history linked to this session. Users can start a new session by joining
    again, which creates a fresh row.
    """

    __tablename__ = "user_group_accumulators"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    group_accumulator_id = Column(
        UUID(as_uuid=True),
        ForeignKey("group_accumulators.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(_datetime.timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(_datetime.timezone.utc),
        onupdate=lambda: datetime.now(_datetime.timezone.utc),
    )
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    history_rows = relationship("GroupAccumulatorHistory", back_populates="user_group_accumulator")

    __table_args__ = (
        Index(
            "idx_user_group_accumulators_group_user",
            "group_accumulator_id",
            "user_id",
        ),
        Index("idx_user_group_accumulators_user", "user_id"),
    )
