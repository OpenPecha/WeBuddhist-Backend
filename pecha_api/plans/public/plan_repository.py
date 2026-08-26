from sqlalchemy.orm import Session, selectinload
from sqlalchemy import and_, exists, func, desc, asc, or_, select
from typing import Optional, Tuple, List
from uuid import UUID
from pecha_api.plans.plans_models import Plan
from pecha_api.plans.series.series_model import Series
from pecha_api.plans.groups.groups_models import author_group_plans, author_group_series
from pecha_api.plans.tags.tag_model import Tag, plan_tags
from pecha_api.plans.items.plan_items_models import PlanItem
from pecha_api.plans.users.plan_users_models import UserPlanProgress
from pecha_api.plans.plans_enums import PlanStatus
from pecha_api.plans.language_constants import SUPPORTED_LANGUAGE_CODES
from pecha_api.plans.public.plan_response_models import PlanWithAggregates

DEFAULT_SKIP = 0
DEFAULT_LIMIT = 20
DEFAULT_LANGUAGE = "EN"
DEFAULT_SEARCH = None
DEFAULT_SORT_BY = "title"
DEFAULT_SORT_ORDER = "asc"
DEFAULT_TAG = None
DEFAULT_GROUP_ID = None


def storable_language(language: str) -> Optional[str]:

    requested = language.upper()
    return requested if requested in SUPPORTED_LANGUAGE_CODES else None


def _with_language_fallback(query, language: Optional[str], fetch):

    if not language:
        return fetch(query)

    requested = storable_language(language)
    if requested is None:
        return fetch(query.filter(Plan.language == DEFAULT_LANGUAGE))

    result = fetch(query.filter(Plan.language == requested))
    if result or requested == DEFAULT_LANGUAGE:
        return result
    return fetch(query.filter(Plan.language == DEFAULT_LANGUAGE))


def resolve_plans_language(db: Session, language: Optional[str]) -> str:

    if not language:
        return DEFAULT_LANGUAGE

    requested = storable_language(language)
    if requested is None or requested == DEFAULT_LANGUAGE:
        return DEFAULT_LANGUAGE

    has_plans = db.query(
        exists(
            select(1).where(
                and_(
                    Plan.language == requested,
                    Plan.deleted_at.is_(None),
                    Plan.status == PlanStatus.PUBLISHED,
                )
            )
        )
    ).scalar()
    return requested if has_plans else DEFAULT_LANGUAGE


def _series_published_or_standalone():
    """Visibility gate for the series a plan belongs to.

    A plan is publicly visible only if it is standalone (``series_id IS NULL``)
    or its parent series is itself ``PUBLISHED``. This prevents a ``PUBLISHED``
    plan that lives under a ``DRAFT`` series (e.g. a freshly cloned series)
    from leaking to end-users before the series is published.
    """
    return or_(
        Plan.series_id.is_(None),
        exists(
            select(1).where(
                and_(
                    Series.id == Plan.series_id,
                    Series.status == PlanStatus.PUBLISHED,
                )
            )
        ),
    )


def get_aggregate_counts():
    total_days_label = func.count(func.distinct(PlanItem.id)).label("total_days")
    subscription_count_label = func.count(func.distinct(UserPlanProgress.user_id)).label("subscription_count")
    return total_days_label, subscription_count_label


def get_published_plans_query(db: Session, total_days_label, subscription_count_label, language: str):
    query = (
        db.query(Plan, total_days_label, subscription_count_label)
        .outerjoin(PlanItem, PlanItem.plan_id == Plan.id)
        .outerjoin(UserPlanProgress, UserPlanProgress.plan_id == Plan.id)
        .options(selectinload(Plan.author), selectinload(Plan.tag_list))
        .filter(
            Plan.language == language,
            Plan.deleted_at.is_(None),
            Plan.status == PlanStatus.PUBLISHED,
            _series_published_or_standalone(),
        )
        .group_by(Plan.id)
    )
    
    return query


def apply_search_filter(query, search: Optional[str]):
    if search:
        query = query.filter(Plan.title.ilike(f"%{search}%"))
    return query

def apply_tag_filter(query, tag: Optional[str]):
    if tag:
        query = (
            query.join(plan_tags, plan_tags.c.plan_id == Plan.id)
            .join(Tag, Tag.id == plan_tags.c.tag_id)
            .filter(Tag.deleted_at.is_(None), func.lower(Tag.name) == tag.lower())
        )
    return query


def apply_group_filter(query, group_id: Optional[UUID]):
    if group_id:
        direct_plan_exists = exists(
            select(1).where(
                and_(
                    author_group_plans.c.group_id == group_id,
                    author_group_plans.c.plan_id == Plan.id,
                )
            )
        )
        series_plan_exists = exists(
            select(1).where(
                and_(
                    author_group_series.c.group_id == group_id,
                    author_group_series.c.series_id == Plan.series_id,
                )
            )
        )
        query = query.filter(or_(direct_plan_exists, series_plan_exists))
    return query

def apply_sorting(query, sort_by: str, sort_order: str, total_days_label, subscription_count_label):
    sort_column_map = {
        "title": Plan.title,
        "total_days": total_days_label,
        "subscription_count": subscription_count_label
    }
    
    sort_column = sort_column_map.get(sort_by, Plan.title)
    
    if sort_order == "desc":
        return query.order_by(desc(sort_column))
    else:
        return query.order_by(asc(sort_column))


def convert_to_plan_aggregates(rows):
    return [
        PlanWithAggregates(plan=plan, total_days=total_days, subscription_count=subscription_count)
        for plan, total_days, subscription_count in rows
    ]


def get_published_plans_from_db(db: Session, 
    skip: int = DEFAULT_SKIP, 
    limit: int = DEFAULT_LIMIT, 
    search: Optional[str] = DEFAULT_SEARCH, 
    language: str = DEFAULT_LANGUAGE,  
    sort_by: str = DEFAULT_SORT_BY,
    sort_order: str = DEFAULT_SORT_ORDER,
    tag: Optional[str] = DEFAULT_TAG,
    group_id: Optional[UUID] = DEFAULT_GROUP_ID,
):
    total_days_label, subscription_count_label = get_aggregate_counts()
    query = get_published_plans_query(db, total_days_label, subscription_count_label, language)
    query = apply_search_filter(query, search)
    query = apply_tag_filter(query, tag)
    query = apply_group_filter(query, group_id)
    query = apply_sorting(query, sort_by, sort_order, total_days_label, subscription_count_label)
    rows = query.offset(skip).limit(limit).all()
    
    return convert_to_plan_aggregates(rows)


def get_published_plans_count(
    db: Session,
    search: Optional[str] = DEFAULT_SEARCH,
    language: str = DEFAULT_LANGUAGE,
    tag: Optional[str] = DEFAULT_TAG,
    group_id: Optional[UUID] = DEFAULT_GROUP_ID,
) -> int:
    query = db.query(func.count(Plan.id)).filter(
        Plan.deleted_at.is_(None),
        Plan.status == PlanStatus.PUBLISHED,
        Plan.language == language,
        _series_published_or_standalone(),
    )
    if search:
        query = query.filter(Plan.title.ilike(f"%{search}%"))
    if tag:
        query = (
            query.join(plan_tags, plan_tags.c.plan_id == Plan.id)
            .join(Tag, Tag.id == plan_tags.c.tag_id)
            .filter(Tag.deleted_at.is_(None), func.lower(Tag.name) == tag.lower())
        )
    query = apply_group_filter(query, group_id)
    return query.scalar()


def get_published_plan_by_id(db: Session, plan_id: UUID) -> Optional[Plan]:
    return db.query(Plan).options(selectinload(Plan.author), selectinload(Plan.tag_list)).filter(
            Plan.id == plan_id,
            Plan.status == PlanStatus.PUBLISHED,
            Plan.deleted_at.is_(None),
            _series_published_or_standalone(),
        ).first()


def get_published_plans_in_series(
    db: Session,
    series_id: UUID,
    language: Optional[str] = None,
) -> List[Plan]:
    query = (
        db.query(Plan)
        .options(
            selectinload(Plan.series).selectinload(Series.metadata_entries),
        )
        .filter(
            Plan.series_id == series_id,
            Plan.display_order.isnot(None),
            Plan.status == PlanStatus.PUBLISHED,
            Plan.deleted_at.is_(None),
            _series_published_or_standalone(),
        )
    )
    return _with_language_fallback(
        query,
        language,
        lambda q: q.order_by(asc(Plan.display_order)).all(),
    )


def get_plan_items_by_plan_id(db: Session, plan_id: UUID) -> list[PlanItem]:
    return db.query(PlanItem).filter(PlanItem.plan_id == plan_id).order_by(PlanItem.day_number).all()


def get_plan_item_by_day_number(db: Session, plan_id: UUID, day_number: int) -> Optional[PlanItem]:
    return db.query(PlanItem).filter(
            PlanItem.plan_id == plan_id,
            PlanItem.day_number == day_number
        ).first()

def get_published_plans_by_author_id(db: Session, author_id: UUID, skip: int, limit: int) -> Tuple[List[PlanWithAggregates], int]:
    total_days_label = func.count(func.distinct(PlanItem.id)).label("total_days")
    subscription_count_label = func.count(func.distinct(UserPlanProgress.user_id)).label("subscription_count")
    query = (
        db.query(
            Plan,
            total_days_label,
            subscription_count_label
        )
        .outerjoin(PlanItem, PlanItem.plan_id == Plan.id)
        .outerjoin(UserPlanProgress, UserPlanProgress.plan_id == Plan.id)
        .filter(
            Plan.author_id == author_id,
            Plan.status == PlanStatus.PUBLISHED,
            Plan.deleted_at.is_(None),
            _series_published_or_standalone(),
        )
        .group_by(Plan.id)
    )
    total = query.count()
    rows = query.offset(skip).limit(limit).all()
    return convert_to_plan_aggregates(rows), total


def get_all_unique_tags(db: Session, language: str = "EN") -> List[str]:
    query = db.query(func.jsonb_array_elements_text(Plan.tags).label("tag")).filter(
        Plan.deleted_at.is_(None),
        Plan.status == PlanStatus.PUBLISHED,
        Plan.language == language,
        _series_published_or_standalone(),
    )
    results = query.distinct().all()
    return [row.tag for row in results]


def get_next_plan_in_series(
    db: Session,
    series_id: UUID,
    current_display_order: Optional[int],
    language: Optional[str] = None,
) -> Optional[Plan]:
    if series_id is None or current_display_order is None:
        return None

    query = db.query(Plan).filter(
        Plan.series_id == series_id,
        Plan.display_order > current_display_order,
        Plan.status == PlanStatus.PUBLISHED,
        Plan.deleted_at.is_(None),
        _series_published_or_standalone(),
    )
    return _with_language_fallback(
        query,
        language,
        lambda q: q.order_by(asc(Plan.display_order)).first(),
    )


def get_previous_plan_in_series(
    db: Session,
    series_id: UUID,
    current_display_order: Optional[int],
    language: Optional[str] = None,
) -> Optional[Plan]:
    if series_id is None or current_display_order is None:
        return None

    query = db.query(Plan).filter(
        Plan.series_id == series_id,
        Plan.display_order < current_display_order,
        Plan.status == PlanStatus.PUBLISHED,
        Plan.deleted_at.is_(None),
        _series_published_or_standalone(),
    )
    return _with_language_fallback(
        query,
        language,
        lambda q: q.order_by(desc(Plan.display_order)).first(),
    )
