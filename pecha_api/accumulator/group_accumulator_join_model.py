from sqlalchemy import Column, DateTime, UUID, ForeignKey, Index, Table, UniqueConstraint
import _datetime
from _datetime import datetime

from ..db.database import Base

group_accumulator_joins = Table(
    "group_accumulator_joins",
    Base.metadata,
    Column(
        "group_accumulator_id",
        UUID(as_uuid=True),
        ForeignKey("group_accumulators.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "user_id",
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "created_at",
        DateTime(timezone=True),
        default=lambda: datetime.now(_datetime.timezone.utc),
        nullable=False,
    ),
    UniqueConstraint(
        "group_accumulator_id",
        "user_id",
        name="uq_group_accumulator_joins_accumulator_user",
    ),
    Index(
        "idx_group_accumulator_joins_accumulator_user",
        "group_accumulator_id",
        "user_id",
    ),
    Index("idx_group_accumulator_joins_user", "user_id"),
)
