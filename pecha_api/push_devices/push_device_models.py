from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID

from pecha_api.db.database import Base
from pecha_api.push_devices.push_device_enums import PushPlatformEnum


class PushDeviceToken(Base):
    __tablename__ = "push_device_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    token = Column(String(512), nullable=False, unique=True)
    platform = Column(PushPlatformEnum, nullable=False)
    device_id = Column(String(255), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        Index("idx_push_device_tokens_user_id", "user_id"),
        Index("idx_push_device_tokens_user_active", "user_id", "is_active"),
        Index(
            "uq_push_device_tokens_user_device_id",
            "user_id",
            "device_id",
            unique=True,
            postgresql_where=(device_id.isnot(None)),
        ),
    )
