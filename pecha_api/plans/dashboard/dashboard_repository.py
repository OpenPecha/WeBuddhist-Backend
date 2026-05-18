import math
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import String, cast, desc, exists, func, literal, or_, select
from sqlalchemy.orm import Query, Session

from pecha_api.plans.authors.plan_authors_model import Author  # noqa: F401
from pecha_api.plans.plans_enums import PlanStatus
from pecha_api.plans.plans_models import Plan
from pecha_api.plans.series.series_model import Series
from pecha_api.plans.users.plan_users_models import UserPlanProgress

_SERIES_TITLE = func.coalesce(
    Series.name["en"].astext,
    Series.name["EN"].astext,
    Series.name["bo"].astext,
    cast(Series.name, String),
)


def _series_plans_count_subquery():
    return (
        select(func.count(Plan.id))
        .where(Plan.series_id == Series.id, Plan.deleted_at.is_(None))
        .correlate(Series)
        .scalar_subquery()
    )


def _series_languages_subquery():
    return (
        select(func.string_agg(func.distinct(cast(Plan.language, String)), ","))
        .where(Plan.series_id == Series.id, Plan.deleted_at.is_(None))
        .correlate(Series)
        .scalar_subquery()
    )


def _series_enrolled_count_subquery():
    return (
        select(func.count(func.distinct(UserPlanProgress.user_id)))
        .select_from(UserPlanProgress)
        .join(Plan, Plan.id == UserPlanProgress.plan_id)
        .where(Plan.series_id == Series.id, Plan.deleted_at.is_(None))
        .correlate(Series)
        .scalar_subquery()
    )


def _plan_enrolled_count_subquery():
    return (
        select(func.count(func.distinct(UserPlanProgress.user_id)))
        .where(UserPlanProgress.plan_id == Plan.id)
        .correlate(Plan)
        .scalar_subquery()
    )


def _apply_series_filters(
    query: Query,
    *,
    search: Optional[str],
    status: Optional[PlanStatus],
    featured: Optional[bool],
    language: Optional[str],
    author_id: Optional[UUID],
) -> Query:
    query = query.filter(Series.deleted_at.is_(None))
    if author_id is not None:
        query = query.filter(Series.author_id == author_id)
    if search:
        query = query.filter(cast(Series.name, String).ilike(f"%{search}%"))
    if status is not None:
        query = query.filter(Series.status == status)
    if featured is not None:
        query = query.filter(Series.featured == featured)
    if language:
        language_upper = language.upper()
        query = query.filter(
            exists(
                select(literal(1)).where(
                    Plan.series_id == Series.id,
                    Plan.deleted_at.is_(None),
                    Plan.language == language_upper,
                )
            )
        )
    return query


def _apply_plan_filters(
    query: Query,
    *,
    search: Optional[str],
    status: Optional[PlanStatus],
    featured: Optional[bool],
    language: Optional[str],
    author_id: Optional[UUID],
    standalone_only: bool,
) -> Query:
    query = query.filter(Plan.deleted_at.is_(None))
    if standalone_only:
        query = query.filter(Plan.series_id.is_(None))
    if author_id is not None:
        query = query.filter(Plan.author_id == author_id)
    if search:
        query = query.filter(
            or_(
                Plan.title.ilike(f"%{search}%"),
                Plan.description.ilike(f"%{search}%"),
            )
        )
    if status is not None:
        query = query.filter(Plan.status == status)
    if featured is not None:
        query = query.filter(Plan.featured == featured)
    if language:
        query = query.filter(Plan.language == language.upper())
    return query


def _series_base_query(db: Session) -> Query:
    return db.query(
        Series.id.label("id"),
        literal("series").label("item_type"),
        _SERIES_TITLE.label("title"),
        Series.image.label("image_key"),
        Series.status.label("status"),
        Series.featured.label("featured"),
        _series_languages_subquery().label("languages_raw"),
        func.coalesce(_series_enrolled_count_subquery(), 0).label("enrolled_count"),
        _series_plans_count_subquery().label("plans_count"),
        Series.updated_at.label("updated_at"),
        Series.created_at.label("created_at"),
    )


def _plan_base_query(db: Session) -> Query:
    return db.query(
        Plan.id.label("id"),
        literal("plan").label("item_type"),
        Plan.title.label("title"),
        Plan.image_url.label("image_key"),
        Plan.status.label("status"),
        Plan.featured.label("featured"),
        cast(Plan.language, String).label("languages_raw"),
        func.coalesce(_plan_enrolled_count_subquery(), 0).label("enrolled_count"),
        literal(None).label("plans_count"),
        Plan.updated_at.label("updated_at"),
        Plan.created_at.label("created_at"),
    )


def _order_combined_query(query: Query, subquery) -> Query:
    return query.order_by(
        desc(subquery.c.featured),
        desc(subquery.c.updated_at),
        subquery.c.item_type,
        subquery.c.id,
    )


def get_dashboard_items(
    db: Session,
    *,
    tab: str,
    page: int,
    page_size: int,
    search: Optional[str],
    status: Optional[PlanStatus],
    language: Optional[str],
    featured: Optional[bool],
    author_id: Optional[UUID],
) -> Tuple[List, int]:
    filter_kwargs = {
        "search": search,
        "status": status,
        "featured": featured,
        "language": language,
        "author_id": author_id,
    }

    series_query = _apply_series_filters(_series_base_query(db), **filter_kwargs)
    plan_query = _apply_plan_filters(
        _plan_base_query(db),
        standalone_only=False,
        **filter_kwargs,
    )
    standalone_plan_query = _apply_plan_filters(
        _plan_base_query(db),
        standalone_only=True,
        **filter_kwargs,
    )

    if tab == "series":
        combined = series_query
    elif tab == "plans":
        combined = plan_query
    else:
        combined = series_query.union_all(standalone_plan_query)

    combined_subquery = combined.subquery()
    ordered = _order_combined_query(db.query(combined_subquery), combined_subquery)

    offset = (page - 1) * page_size
    rows = ordered.offset(offset).limit(page_size).all()

    total = db.query(func.count()).select_from(combined_subquery).scalar() or 0
    return rows, int(total)


def total_pages(total: int, page_size: int) -> int:
    if page_size <= 0:
        return 0
    return math.ceil(total / page_size) if total > 0 else 0
