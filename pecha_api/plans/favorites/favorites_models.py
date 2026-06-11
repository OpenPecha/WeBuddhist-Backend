from sqlalchemy import Column, DateTime, UUID, ForeignKey, Index
from sqlalchemy.orm import relationship, backref
from uuid import uuid4
from ...db.database import Base
from _datetime import datetime
import _datetime


class Favorite(Base):
    __tablename__ = "favorites"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    plan_id = Column(UUID(as_uuid=True), ForeignKey('plans.id', ondelete='CASCADE'), nullable=False)

    created_at = Column(DateTime, default=datetime.now(_datetime.timezone.utc))
    updated_at = Column(DateTime, default=datetime.now(_datetime.timezone.utc))

    user = relationship("Users", backref=backref("favorites", cascade="all, delete-orphan"))

    __table_args__ = (
        Index("idx_favorites_user_plan", "user_id", "plan_id"),
    )


