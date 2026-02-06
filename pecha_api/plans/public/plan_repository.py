from sqlalchemy.orm import Session, selectinload
from sqlalchemy import func, desc, asc
from typing import Optional, Tuple, List
from uuid import UUID
from pecha_api.plans.plans_models import Plan
from pecha_api.plans.items.plan_items_models import PlanItem
from pecha_api.plans.users.plan_users_models import UserPlanProgress
from pecha_api.plans.plans_enums import PlanStatus
from pecha_api.plans.public.plan_response_models import PlanWithAggregates

DEFAULT_SKIP = 0
DEFAULT_LIMIT = 20
DEFAULT_LANGUAGE = "EN"
DEFAULT_SEARCH = None
DEFAULT_SORT_BY = "title"
DEFAULT_SORT_ORDER = "asc"
DEFAULT_TAG = None

def get_aggregate_counts():
    total_days_label = func.count(func.distinct(PlanItem.id)).label("total_days")
    subscription_count_label = func.count(func.distinct(UserPlanProgress.user_id)).label("subscription_count")
    return total_days_label, subscription_count_label


def get_published_plans_query(db: Session, total_days_label, subscription_count_label, language: str):
    query = (
        db.query(Plan, total_days_label, subscription_count_label)
        .outerjoin(PlanItem, PlanItem.plan_id == Plan.id)
        .outerjoin(UserPlanProgress, UserPlanProgress.plan_id == Plan.id)
        .options(selectinload(Plan.author))
        .filter(
            Plan.language == language,
            Plan.deleted_at.is_(None),
            Plan.status == PlanStatus.PUBLISHED
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
        query = query.filter(Plan.tags.contains([tag]))
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
    tag: Optional[str] = DEFAULT_TAG
):
    total_days_label, subscription_count_label = get_aggregate_counts()
    query = get_published_plans_query(db, total_days_label, subscription_count_label, language)
    query = apply_search_filter(query, search)
    query = apply_tag_filter(query, tag)
    query = apply_sorting(query, sort_by, sort_order, total_days_label, subscription_count_label)
    rows = query.offset(skip).limit(limit).all()
    
    return convert_to_plan_aggregates(rows)


def get_published_plans_count(db: Session, search: Optional[str] = DEFAULT_SEARCH, language: str = DEFAULT_LANGUAGE, tag: Optional[str] = DEFAULT_TAG) -> int:
    query = db.query(func.count(Plan.id)).filter(
        Plan.deleted_at.is_(None),
        Plan.status == PlanStatus.PUBLISHED,
        Plan.language == language
    )
    if search:
        query = query.filter(Plan.title.ilike(f"%{search}%"))
    if tag:
        query = query.filter(Plan.tags.contains([tag]))
    return query.scalar()


def get_published_plan_by_id(db: Session, plan_id: UUID) -> Optional[Plan]:
    return db.query(Plan).options(selectinload(Plan.author)).filter(
            Plan.id == plan_id,
            Plan.status == PlanStatus.PUBLISHED,
            Plan.deleted_at.is_(None)
        ).first()


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
        .filter(Plan.author_id == author_id, Plan.status == PlanStatus.PUBLISHED, Plan.deleted_at.is_(None))
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
    )
    results = query.distinct().all()
    return [row.tag for row in results]
