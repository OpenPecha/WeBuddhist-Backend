from datetime import date, datetime, time, timedelta, timezone
from typing import List, Optional, Sequence, Tuple
from uuid import UUID

from sqlalchemy import Date, Integer, case, cast, func, select
from sqlalchemy.orm import Session

from pecha_api.plans.plans_enums import LanguageCode
from pecha_api.plans.plans_models import Plan
from pecha_api.plans.series.series_metadata_model import SeriesMetadata
from pecha_api.plans.users.plan_users_models import UserPlanProgress
from pecha_api.users.users_models import Users


def as_utc_start(day: date) -> datetime:
    return datetime.combine(day, time.min, tzinfo=timezone.utc)


def as_utc_end_exclusive(day: date) -> datetime:
    return datetime.combine(day + timedelta(days=1), time.min, tzinfo=timezone.utc)


def as_naive_utc(day: date) -> datetime:
    """Users.created_at is stored without timezone; compare as naive UTC."""
    return datetime.combine(day, time.min)


def as_naive_utc_end_exclusive(day: date) -> datetime:
    return datetime.combine(day + timedelta(days=1), time.min)


def count_total_users(db: Session) -> int:
    return int(db.query(func.count(Users.id)).scalar() or 0)


def count_new_users_between(
    db: Session,
    *,
    start: datetime,
    end_exclusive: datetime,
) -> int:
    return int(
        db.query(func.count(Users.id))
        .filter(Users.created_at >= start, Users.created_at < end_exclusive)
        .scalar()
        or 0
    )


def get_user_growth_by_day(
    db: Session,
    *,
    start: datetime,
    end_exclusive: datetime,
) -> List[Tuple[date, int]]:
    day_col = cast(Users.created_at, Date).label("day")
    rows = (
        db.query(day_col, func.count(Users.id))
        .filter(Users.created_at >= start, Users.created_at < end_exclusive)
        .group_by(day_col)
        .order_by(day_col)
        .all()
    )
    return [(row[0], int(row[1] or 0)) for row in rows]


def get_joins_by_day(
    db: Session,
    *,
    start: datetime,
    end_exclusive: datetime,
    group_ids: Optional[Sequence[UUID]] = None,
) -> List[Tuple[date, int]]:
    day_col = cast(UserPlanProgress.started_at, Date).label("day")
    query = (
        db.query(day_col, func.count(UserPlanProgress.id))
        .join(Plan, Plan.id == UserPlanProgress.plan_id)
        .filter(
            Plan.deleted_at.is_(None),
            UserPlanProgress.started_at >= start,
            UserPlanProgress.started_at < end_exclusive,
        )
    )
    if group_ids is not None:
        query = query.filter(Plan.group_id.in_(group_ids))
    rows = query.group_by(day_col).order_by(day_col).all()
    return [(row[0], int(row[1] or 0)) for row in rows]


def get_completions_by_day(
    db: Session,
    *,
    start: datetime,
    end_exclusive: datetime,
    group_ids: Optional[Sequence[UUID]] = None,
) -> List[Tuple[date, int]]:
    day_col = cast(UserPlanProgress.completed_at, Date).label("day")
    query = (
        db.query(day_col, func.count(UserPlanProgress.id))
        .join(Plan, Plan.id == UserPlanProgress.plan_id)
        .filter(
            Plan.deleted_at.is_(None),
            UserPlanProgress.is_completed.is_(True),
            UserPlanProgress.completed_at.isnot(None),
            UserPlanProgress.completed_at >= start,
            UserPlanProgress.completed_at < end_exclusive,
        )
    )
    if group_ids is not None:
        query = query.filter(Plan.group_id.in_(group_ids))
    rows = query.group_by(day_col).order_by(day_col).all()
    return [(row[0], int(row[1] or 0)) for row in rows]


def _series_title_subquery():
    return (
        select(SeriesMetadata.title)
        .where(SeriesMetadata.series_id == Plan.series_id)
        .order_by(
            case((SeriesMetadata.language == LanguageCode.EN, 0), else_=1),
            SeriesMetadata.language.asc(),
        )
        .limit(1)
        .correlate(Plan)
        .scalar_subquery()
    )


def get_top_plans(
    db: Session,
    *,
    start: datetime,
    end_exclusive: datetime,
    limit: int = 10,
    group_ids: Optional[Sequence[UUID]] = None,
) -> List:
    join_count = func.count(UserPlanProgress.id).label("join_count")
    completion_count = func.coalesce(
        func.sum(
            case(
                (UserPlanProgress.is_completed.is_(True), cast(1, Integer)),
                else_=cast(0, Integer),
            )
        ),
        0,
    ).label("completion_count")
    series_name = _series_title_subquery().label("series_name")

    query = (
        db.query(
            Plan.id,
            Plan.title,
            Plan.series_id,
            series_name,
            join_count,
            completion_count,
        )
        .join(UserPlanProgress, UserPlanProgress.plan_id == Plan.id)
        .filter(
            Plan.deleted_at.is_(None),
            UserPlanProgress.started_at >= start,
            UserPlanProgress.started_at < end_exclusive,
        )
        .group_by(Plan.id, Plan.title, Plan.series_id)
        .order_by(join_count.desc(), completion_count.desc(), Plan.title.asc())
        .limit(limit)
    )
    if group_ids is not None:
        query = query.filter(Plan.group_id.in_(group_ids))
    return query.all()
