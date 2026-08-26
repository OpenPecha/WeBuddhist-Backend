from datetime import date, datetime, timezone

from sqlalchemy import Column, Date, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4

from pecha_api.db.database import Base


class UserDailyLog(Base):
    __tablename__ = "user_daily_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    log_date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("user_id", "log_date", name="uq_user_daily_logs_user_date"),
        Index("idx_user_daily_logs_user_id", "user_id"),
        Index("idx_user_daily_logs_user_date", "user_id", "log_date"),
    )
