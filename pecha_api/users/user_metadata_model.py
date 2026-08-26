from sqlalchemy import Column, String, DateTime, UUID, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from ..db.database import Base
from ..plans.plans_enums import LanguageCodeEnum
from uuid import uuid4
import _datetime
from _datetime import datetime


class UserMetadata(Base):
    __tablename__ = "user_metadata"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)
    language = Column(LanguageCodeEnum, nullable=False, server_default="EN")
    timezone = Column(String(64), nullable=False, server_default="Asia/Kathmandu")
    created_at = Column(DateTime(timezone=True), default=datetime.now(_datetime.timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.now(_datetime.timezone.utc), nullable=False)

    user = relationship("Users", backref="metadata")

    __table_args__ = (
        UniqueConstraint("user_id", name="uq_user_metadata_user_id"),
    )
