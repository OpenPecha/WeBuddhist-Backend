from sqlalchemy import Column, Integer, DateTime, Boolean, Text, ForeignKey, Index, UniqueConstraint, UUID, CheckConstraint, text,String
from sqlalchemy.orm import relationship, backref
from uuid import uuid4
from ...db.database import Base
from _datetime import datetime
import _datetime


class PlanReview(Base):
    __tablename__ = "reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    plan_id = Column(UUID(as_uuid=True), ForeignKey('plans.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    rating = Column(Integer, nullable=False)
    review_text = Column(Text, nullable=True)

    is_approved = Column(Boolean, default=False)
    approved_by = Column(String(255))

    created_at = Column(DateTime(timezone=True), default=datetime.now(_datetime.timezone.utc))
    created_by = Column(String(255), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.now(_datetime.timezone.utc))
    updated_by = Column(String(255))

    deleted_at = Column(DateTime(timezone=True))
    deleted_by = Column(String(255))

    user = relationship("Users", backref=backref("reviews", cascade="all, delete-orphan"))

    __table_args__ = (
        UniqueConstraint("user_id", "plan_id", name="uq_plan_reviews_user_plan"),
        CheckConstraint("rating >= 1 AND rating <= 5", name="chk_plan_reviews_rating"),
        Index("idx_plan_reviews_plan_approved", "plan_id", "is_approved", postgresql_where=text("is_approved = TRUE")),
        Index("idx_plan_reviews_rating", "plan_id", "rating"),
    )


