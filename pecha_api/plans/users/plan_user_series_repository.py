from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, asc
from datetime import datetime, timezone

from .plan_users_models import UserSeriesEnrollment
from ..plans_models import Plan
from ..plans_enums import SeriesStatus
from ..public.plan_repository import get_next_plan_in_series as get_next_plan_by_display_order


def save_user_series_enrollment(db: Session, enrollment: UserSeriesEnrollment) -> UserSeriesEnrollment:
    """Save a new user series enrollment"""
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    return enrollment


def get_user_series_enrollment_by_user_and_series(
    db: Session, user_id: UUID, series_id: UUID
) -> Optional[UserSeriesEnrollment]:
    """Get user series enrollment by user and series ID"""
    return db.query(UserSeriesEnrollment).filter(
        and_(
            UserSeriesEnrollment.user_id == user_id,
            UserSeriesEnrollment.series_id == series_id
        )
    ).first()


def get_user_series_enrollments_by_user_id(
    db: Session,
    user_id: UUID,
    status_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
) -> Tuple[List[UserSeriesEnrollment], int]:
    """Get all series enrollments for a user with pagination"""
    query = db.query(UserSeriesEnrollment).filter(UserSeriesEnrollment.user_id == user_id)

    if status_filter:
        query = query.filter(UserSeriesEnrollment.status == status_filter)

    total = query.count()

    enrollments = query.order_by(desc(UserSeriesEnrollment.enrolled_at)).offset(skip).limit(limit).all()

    return enrollments, total


def update_user_series_enrollment(
    db: Session,
    enrollment: UserSeriesEnrollment
) -> UserSeriesEnrollment:
    """Update an existing series enrollment"""
    enrollment.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(enrollment)
    return enrollment


def delete_user_series_enrollment(db: Session, user_id: UUID, series_id: UUID) -> bool:
    """Delete a user series enrollment"""
    result = db.query(UserSeriesEnrollment).filter(
        and_(
            UserSeriesEnrollment.user_id == user_id,
            UserSeriesEnrollment.series_id == series_id
        )
    ).delete()
    db.commit()
    return result > 0


def mark_series_enrollment_completed(
    db: Session,
    user_id: UUID,
    series_id: UUID
) -> Optional[UserSeriesEnrollment]:
    """Mark a series enrollment as completed"""
    enrollment = get_user_series_enrollment_by_user_and_series(db, user_id, series_id)
    if enrollment:
        enrollment.status = SeriesStatus.COMPLETED
        enrollment.is_completed = True
        enrollment.completed_at = datetime.now(timezone.utc)
        enrollment.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(enrollment)
    return enrollment


def update_current_plan_in_series(
    db: Session,
    user_id: UUID,
    series_id: UUID,
    current_plan_id: Optional[UUID]
) -> Optional[UserSeriesEnrollment]:
    """Update the current active plan in a series enrollment"""
    enrollment = get_user_series_enrollment_by_user_and_series(db, user_id, series_id)
    if enrollment:
        enrollment.current_plan_id = current_plan_id
        enrollment.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(enrollment)
    return enrollment


def get_plans_by_series_id(db: Session, series_id: UUID) -> List[Plan]:
    """Get all plans in a series ordered by display_order on the plan."""
    return (
        db.query(Plan)
        .filter(
            Plan.series_id == series_id,
            Plan.display_order.isnot(None),
            Plan.deleted_at.is_(None),
        )
        .order_by(asc(Plan.display_order))
        .all()
    )


def get_first_plan_in_series(db: Session, series_id: UUID) -> Optional[Plan]:
    """Get the first plan in a series by display_order."""
    plans = get_plans_by_series_id(db, series_id)
    return plans[0] if plans else None


def get_next_plan_in_series(
    db: Session,
    series_id: UUID,
    current_plan_id: UUID,
) -> Optional[Plan]:
    """Get the next plan in series after the current plan."""
    current_plan = db.query(Plan).filter(Plan.id == current_plan_id).first()
    if not current_plan or current_plan.display_order is None:
        return None

    return get_next_plan_by_display_order(
        db=db,
        series_id=series_id,
        current_display_order=current_plan.display_order,
    )


def is_series_completed_for_user(db: Session, user_id: UUID, series_id: UUID) -> bool:
    """Check if user has completed all plans in a series."""
    plans = get_plans_by_series_id(db, series_id)
    if not plans:
        return False

    from .plan_users_progress_repository import get_plan_progress_by_user_id_and_plan_id

    for plan in plans:
        progress = get_plan_progress_by_user_id_and_plan_id(db, user_id, plan.id)
        if not progress or not progress.is_completed:
            return False

    return True
