from collections import defaultdict
from typing import Dict, List, Optional, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, asc
from datetime import datetime, timezone

from .plan_users_models import UserSeriesEnrollment, SeriesPartner
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


def get_series_partner(db: Session, series_id: UUID, group_id: UUID) -> Optional[SeriesPartner]:
    """Return the series_partner row for the given series and group, if the group is its partner."""
    return db.query(SeriesPartner).filter(
        and_(
            SeriesPartner.series_id == series_id,
            SeriesPartner.group_id == group_id,
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
    return get_plans_by_series_ids(db, [series_id]).get(series_id, [])


def get_plans_by_series_ids(db: Session, series_ids: List[UUID]) -> Dict[UUID, List[Plan]]:
    """Get all plans for multiple series, grouped by series_id and ordered by display_order."""
    if not series_ids:
        return {}
    plans = (
        db.query(Plan)
        .filter(
            Plan.series_id.in_(series_ids),
            Plan.display_order.isnot(None),
            Plan.deleted_at.is_(None),
        )
        .order_by(Plan.series_id, asc(Plan.display_order))
        .all()
    )
    plans_by_series: Dict[UUID, List[Plan]] = defaultdict(list)
    for plan in plans:
        plans_by_series[plan.series_id].append(plan)
    return dict(plans_by_series)


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


def get_user_series_enrollments_for_plans(
    db: Session,
    user_id: UUID,
    status_filter: Optional[str] = None,
) -> List[UserSeriesEnrollment]:
    query = db.query(UserSeriesEnrollment).filter(
        UserSeriesEnrollment.user_id == user_id
    )
    
    if status_filter:
        query = query.filter(UserSeriesEnrollment.status == status_filter)
    
    return query.order_by(desc(UserSeriesEnrollment.enrolled_at)).all()


def get_plans_by_series_ids_with_tags(
    db: Session,
    series_ids: List[UUID]
) -> List[Plan]:
    from sqlalchemy.orm import selectinload
    
    if not series_ids:
        return []
    
    return (
        db.query(Plan)
        .options(selectinload(Plan.tag_list))
        .filter(
            Plan.series_id.in_(series_ids),
            Plan.deleted_at.is_(None),
        )
        .all()
    )


def get_paginated_plans_from_enrolled_series(
    db: Session,
    user_id: UUID,
    status_filter: Optional[str] = None,
    series_id: Optional[UUID] = None,
    language: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
) -> Tuple[List[Plan], int]:
    from sqlalchemy.orm import selectinload
    from sqlalchemy import func, case, literal
    
    enrollment_query = db.query(
        UserSeriesEnrollment.series_id,
        UserSeriesEnrollment.enrolled_at
    ).filter(
        UserSeriesEnrollment.user_id == user_id
    )
    
    if status_filter:
        enrollment_query = enrollment_query.filter(
            UserSeriesEnrollment.status == status_filter
        )
    
    if series_id:
        enrollment_query = enrollment_query.filter(
            UserSeriesEnrollment.series_id == series_id
        )
    
    enrollment_subquery = enrollment_query.subquery()
    
    # Get all plans from enrolled series
    plans_query = (
        db.query(Plan)
        .join(enrollment_subquery, Plan.series_id == enrollment_subquery.c.series_id)
        .filter(Plan.deleted_at.is_(None))
        .options(selectinload(Plan.tag_list))
        .order_by(
            enrollment_subquery.c.series_id,
            asc(func.coalesce(Plan.display_order, 999))
        )
    )
    if language:
        plans_query = plans_query.filter(Plan.language == language.upper())
    all_plans_query = plans_query.all()
    
    if not all_plans_query:
        return [], 0
    
    # Filter plans based on date availability - only prior and current active plans
    filtered_plans = _filter_plans_by_date_availability(all_plans_query)
    
    # Apply pagination to filtered results
    total = len(filtered_plans)
    start_index = skip
    end_index = skip + limit
    paginated_plans = filtered_plans[start_index:end_index]
    
    return paginated_plans, total


def _filter_plans_by_date_availability(plans: List[Plan]) -> List[Plan]:
    """
    Filter plans to only include:
    1. Plans with display_order > 0 (first plan in a series is excluded from /users/me/plans)
    2. Prior plans: Plans that have started and either completed or should have been completed (next plan started)
    3. Current active plans: Plans that are currently active (started but next plan hasn't started)
    """
    from datetime import datetime, timezone
    
    today = datetime.now(timezone.utc).date()
    available_plans = []
    
    # Group plans by series for better processing
    series_plans = {}
    for plan in plans:
        if plan.series_id not in series_plans:
            series_plans[plan.series_id] = []
        series_plans[plan.series_id].append(plan)
    
    # Process each series separately
    for series_plan_list in series_plans.values():
        # Sort by display order to process in sequence
        sorted_plans = sorted(series_plan_list, key=lambda p: p.display_order or 999)
        
        for i, plan in enumerate(sorted_plans):
            if plan.display_order == 0:
                continue

            if not plan.start_date:
                # Plans without start date are not date-restricted, skip them
                continue
            
            plan_start_date = plan.start_date.date() if hasattr(plan.start_date, 'date') else plan.start_date
            
            # Skip plans that haven't started yet
            if today < plan_start_date:
                continue
            
            # Look for the next plan in sequence to determine if current plan is still active
            # If next plan has started, current plan becomes a "prior" plan
            # If next plan hasn't started, current plan is still "active"
            if i + 1 < len(sorted_plans):
                next_plan = sorted_plans[i + 1]
                if next_plan.start_date:
                    next_plan_start_date = next_plan.start_date.date() if hasattr(next_plan.start_date, 'date') else next_plan.start_date
                    # Whether next plan has started or not, we include current plan
                    # as it's either prior (completed/should be completed) or currently active
            
            # Include the plan if it's either:
            # 1. A prior plan (has started, and next plan has also started)
            # 2. A current active plan (has started, but next plan hasn't started yet)
            available_plans.append(plan)
    
    return available_plans
