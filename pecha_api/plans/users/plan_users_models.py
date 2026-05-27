from sqlalchemy import Column, DateTime, Boolean, Integer, Index, UniqueConstraint, UUID, ForeignKey, String
from uuid import uuid4
from _datetime import datetime
import _datetime
from sqlalchemy.orm import relationship

from ...db.database import Base
from ...plans.plans_enums import UserPlanStatusEnum, EnrollmentSourceEnum, SeriesStatusEnum


class UserPlanProgress(Base):
    __tablename__ = "user_plan_progress"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    plan_id = Column(UUID(as_uuid=True), ForeignKey('plans.id', ondelete='CASCADE'), nullable=False)

    # New fields for series enrollment tracking
    enrollment_source = Column(EnrollmentSourceEnum, default='DIRECT', nullable=False)
    series_enrollment_id = Column(UUID(as_uuid=True), ForeignKey('user_series_enrollment.id', ondelete='CASCADE'), nullable=True)
    auto_enrolled = Column(Boolean, default=False, nullable=False)
    auto_enrolled_at = Column(DateTime(timezone=True), nullable=True)

    started_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(_datetime.timezone.utc),
    )

    streak_count = Column(Integer, default=0)
    longest_streak = Column(Integer, default=0)

    status = Column(UserPlanStatusEnum, default='ACTIVE')
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(_datetime.timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(_datetime.timezone.utc),
    )

    user = relationship("Users", backref="plan_progress")
    series_enrollment = relationship("UserSeriesEnrollment", back_populates="plan_progress_records")

    __table_args__ = (
        UniqueConstraint("user_id", "plan_id", name="uq_user_plan_progress_user_plan"),
        Index("idx_user_progress_user_status", "user_id", "status"),
        Index("idx_user_progress_plan", "plan_id"),
        Index("idx_user_progress_series_enrollment", "series_enrollment_id"),
        Index("idx_user_progress_enrollment_source", "enrollment_source"),
    )


class UserTaskCompletion(Base):
    __tablename__ = "user_task_completion"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    task_id = Column(UUID(as_uuid=True), ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False)

    completed_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(_datetime.timezone.utc),
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(_datetime.timezone.utc),
        nullable=False,
    )

    user = relationship("Users", backref="completed_tasks")
    task = relationship("PlanTask", back_populates="user_task_completions")

    __table_args__ = (
        UniqueConstraint("user_id", "task_id", name="uq_user_task_completion"),
        Index("idx_user_completion_user_task", "user_id", "task_id"),
        Index("idx_user_completion_completed_at", "completed_at"),
    )


class UserDayCompletion(Base):
    __tablename__ = "user_day_completion"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    day_id = Column(UUID(as_uuid=True), ForeignKey('items.id', ondelete='CASCADE'), nullable=False)
    completed_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(_datetime.timezone.utc),
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(_datetime.timezone.utc),
        nullable=False,
    )

    user = relationship("Users", backref="day_completions")
    item = relationship("PlanItem", backref="user_day_completions")

    __table_args__ = (
        UniqueConstraint("user_id", "day_id", name="uq_user_day_completion"),
        Index("idx_user_day_completion_user_day", "user_id", "day_id"),
        Index("idx_user_day_completion_completed_at", "completed_at"),
    )

class UserSubTaskCompletion(Base):
    __tablename__ = "user_sub_task_completion"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    sub_task_id = Column(UUID(as_uuid=True), ForeignKey('sub_tasks.id', ondelete='CASCADE'), nullable=False)
    completed_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(_datetime.timezone.utc),
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(_datetime.timezone.utc),
        nullable=False,
    )

    user = relationship("Users", backref="sub_task_completions")
    sub_task = relationship("PlanSubTask", back_populates="user_sub_task_completions")

    __table_args__ = (
        UniqueConstraint("user_id", "sub_task_id", name="uq_user_sub_task_completion"),
        Index("idx_user_sub_task_completion_user_sub_task", "user_id", "sub_task_id"),
        Index("idx_user_sub_task_completion_completed_at", "completed_at"),
    )


class UserSeriesEnrollment(Base):
    __tablename__ = "user_series_enrollment"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    series_id = Column(UUID(as_uuid=True), ForeignKey('series.id', ondelete='CASCADE'), nullable=False)
    
    enrolled_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(_datetime.timezone.utc),
    )
    
    status = Column(SeriesStatusEnum, default='ACTIVE', nullable=False)
    auto_enroll_next = Column(Boolean, default=True, nullable=False)
    current_plan_id = Column(UUID(as_uuid=True), ForeignKey('plans.id', ondelete='SET NULL'), nullable=True)
    
    # Completion tracking
    is_completed = Column(Boolean, default=False, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(_datetime.timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(_datetime.timezone.utc),
    )

    # Relationships
    user = relationship("Users", backref="series_enrollments")
    series = relationship("Series", backref="user_enrollments")
    current_plan = relationship("Plan", foreign_keys=[current_plan_id])
    plan_progress_records = relationship("UserPlanProgress", back_populates="series_enrollment")

    __table_args__ = (
        UniqueConstraint("user_id", "series_id", name="uq_user_series_enrollment"),
        Index("idx_user_series_enrollment_user_status", "user_id", "status"),
        Index("idx_user_series_enrollment_series", "series_id"),
        Index("idx_user_series_enrollment_current_plan", "current_plan_id"),
    )