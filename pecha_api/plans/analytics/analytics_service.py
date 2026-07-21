from calendar import monthrange
from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Optional, Sequence
from uuid import UUID

from fastapi import HTTPException
from starlette import status

from pecha_api.db.database import SessionLocal
from pecha_api.plans.analytics import analytics_repository as repo
from pecha_api.plans.analytics.analytics_response_models import (
    AnalyticsDateRangeDTO,
    AnalyticsOverviewResponse,
    AnalyticsTimePointDTO,
    AnalyticsTopPlanDTO,
    AnalyticsUserStatsDTO,
)
from pecha_api.plans.authors.plan_authors_model import Author
from pecha_api.plans.authors.plan_authors_service import validate_cms_author_details
from pecha_api.plans.groups.groups_repository import get_author_group_ids
from pecha_api.plans.shared.permissions import (
    is_reviewer,
    is_super_admin,
    require_can_read_group_content,
)
from sqlalchemy.orm import Session

_MAX_RANGE_DAYS = 366


def _resolve_analytics_group_ids(
    db: Session,
    author: Author,
    group_id: Optional[UUID] = None,
) -> Optional[Sequence[UUID]]:
    if group_id is not None:
        require_can_read_group_content(db=db, group_id=group_id, author=author)
        return [group_id]
    if is_super_admin(author) or is_reviewer(author):
        return None
    return get_author_group_ids(db=db, author_id=author.id)


def _default_date_range(today: Optional[date] = None) -> tuple[date, date]:
    end = today or datetime.now(timezone.utc).date()
    start = end - timedelta(days=29)
    return start, end


def _month_bounds(today: Optional[date] = None) -> tuple[date, date]:
    current = today or datetime.now(timezone.utc).date()
    start = current.replace(day=1)
    last_day = monthrange(current.year, current.month)[1]
    end = current.replace(day=last_day)
    return start, end


def _normalize_date_range(
    start_date: Optional[date],
    end_date: Optional[date],
) -> tuple[date, date]:
    default_start, default_end = _default_date_range()
    start = start_date or default_start
    end = end_date or default_end
    if start > end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date must be on or before end_date",
        )
    if (end - start).days > _MAX_RANGE_DAYS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Date range cannot exceed {_MAX_RANGE_DAYS} days",
        )
    return start, end


def _build_timeline(
    *,
    start: date,
    end: date,
    users_by_day: Dict[date, int],
    joins_by_day: Dict[date, int],
    completions_by_day: Dict[date, int],
) -> List[AnalyticsTimePointDTO]:
    points: List[AnalyticsTimePointDTO] = []
    cursor = start
    while cursor <= end:
        points.append(
            AnalyticsTimePointDTO(
                date=cursor,
                new_users=users_by_day.get(cursor, 0),
                joins=joins_by_day.get(cursor, 0),
                completions=completions_by_day.get(cursor, 0),
            )
        )
        cursor += timedelta(days=1)
    return points


def get_analytics_overview(
    token: str,
    *,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    group_id: Optional[UUID] = None,
    top_limit: int = 10,
) -> AnalyticsOverviewResponse:
    current_author = validate_cms_author_details(token=token)
    start, end = _normalize_date_range(start_date, end_date)
    top_limit = max(1, min(top_limit, 50))

    range_start = repo.as_utc_start(start)
    range_end_exclusive = repo.as_utc_end_exclusive(end)
    month_start_date, month_end_date = _month_bounds()
    month_start = repo.as_utc_start(month_start_date)
    month_end_exclusive = repo.as_utc_end_exclusive(month_end_date)

    users_range_start = repo.as_naive_utc(start)
    users_range_end_exclusive = repo.as_naive_utc_end_exclusive(end)
    users_month_start = repo.as_naive_utc(month_start_date)
    users_month_end_exclusive = repo.as_naive_utc_end_exclusive(month_end_date)

    with SessionLocal() as db:
        group_ids = _resolve_analytics_group_ids(
            db=db,
            author=current_author,
            group_id=group_id,
        )
        empty_scope = group_ids is not None and len(group_ids) == 0

        total_users = repo.count_total_users(db)
        new_users_this_month = repo.count_new_users_between(
            db, start=users_month_start, end_exclusive=users_month_end_exclusive
        )
        new_users_in_range = repo.count_new_users_between(
            db, start=users_range_start, end_exclusive=users_range_end_exclusive
        )

        if empty_scope:
            top_rows = []
            users_by_day: Dict[date, int] = {
                day: count
                for day, count in repo.get_user_growth_by_day(
                    db,
                    start=users_range_start,
                    end_exclusive=users_range_end_exclusive,
                )
            }
            joins_by_day: Dict[date, int] = {}
            completions_by_day: Dict[date, int] = {}
        else:
            top_rows = repo.get_top_plans(
                db,
                start=range_start,
                end_exclusive=range_end_exclusive,
                limit=top_limit,
                group_ids=group_ids,
            )
            users_by_day = {
                day: count
                for day, count in repo.get_user_growth_by_day(
                    db,
                    start=users_range_start,
                    end_exclusive=users_range_end_exclusive,
                )
            }
            joins_by_day = {
                day: count
                for day, count in repo.get_joins_by_day(
                    db,
                    start=range_start,
                    end_exclusive=range_end_exclusive,
                    group_ids=group_ids,
                )
            }
            completions_by_day = {
                day: count
                for day, count in repo.get_completions_by_day(
                    db,
                    start=range_start,
                    end_exclusive=range_end_exclusive,
                    group_ids=group_ids,
                )
            }

    top_plans = [
        AnalyticsTopPlanDTO(
            id=row.id,
            title=row.title or "",
            series_id=row.series_id,
            series_name=row.series_name,
            join_count=int(row.join_count or 0),
            completion_count=int(row.completion_count or 0),
        )
        for row in top_rows
    ]

    return AnalyticsOverviewResponse(
        date_range=AnalyticsDateRangeDTO(start_date=start, end_date=end),
        users=AnalyticsUserStatsDTO(
            total_users=total_users,
            new_users_this_month=new_users_this_month,
            new_users_in_range=new_users_in_range,
        ),
        top_plans=top_plans,
        timeline=_build_timeline(
            start=start,
            end=end,
            users_by_day=users_by_day,
            joins_by_day=joins_by_day,
            completions_by_day=completions_by_day,
        ),
        generated_at=datetime.now(timezone.utc),
    )
