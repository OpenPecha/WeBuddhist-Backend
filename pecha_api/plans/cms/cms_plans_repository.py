from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import func, asc, desc
from typing import Optional
from uuid import UUID
from datetime import datetime, timezone
from pecha_api.plans.authors.plan_authors_model import Author
from pecha_api.plans.plans_models import Plan
from pecha_api.plans.items.plan_items_models import PlanItem
from pecha_api.plans.users.plan_users_models import UserPlanProgress
from fastapi import HTTPException
from starlette import status
from pecha_api.plans.plans_response_models import PlansRepositoryResponse, PlanWithAggregates

def save_plan(db: Session, plan: Plan):
    try:
        db.add(plan)
        db.commit()
        db.refresh(plan)
        return plan
    except IntegrityError as e:
        db.rollback()
        print(f"Integrity error: {e.orig}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{e.orig}")


def get_plans_by_author_id(
    db: Session,
    search: Optional[str],
    author_id: UUID,
    is_admin: bool,
    sort_by: str,
    sort_order: str,
    skip: int,
    limit: int,
) -> PlansRepositoryResponse:
    # Filters
    filters = [Plan.deleted_at.is_(None)]
    if not is_admin:
        filters.append(Plan.author_id == author_id)
    if search:
        filters.append(Plan.title.ilike(f"%{search}%"))

    # Aggregates (matching provided SQL): SUM of item day_number and COUNT DISTINCT of subscribers
    total_days_label = func.count(func.distinct(PlanItem.id)).label("total_days")
    subscription_count_label = func.count(func.distinct(UserPlanProgress.user_id)).label("subscription_count")

    # Base query with LEFT JOINs and GROUP BY
    query = (
        db.query(
            Plan,
            total_days_label,
            subscription_count_label,
        )
        .outerjoin(PlanItem, PlanItem.plan_id == Plan.id)
        .outerjoin(UserPlanProgress, UserPlanProgress.plan_id == Plan.id)
        .options(selectinload(Plan.author))
        .filter(*filters)
        .group_by(Plan.id)
    )

    order_func = asc if sort_order == "asc" else desc
    sort_fields = {
        "created_at": Plan.created_at,
        "status": Plan.status,
        "total_days": total_days_label,
    }
    primary_sort = sort_fields.get(sort_by, Plan.created_at)
    query = query.order_by(order_func(primary_sort), desc(Plan.created_at), Plan.id)

    # Pagination
    rows = query.offset(skip).limit(limit).all()
    
    # Transform tuples into PlanWithAggregates objects using list comprehension
    plan_aggregates = [
        PlanWithAggregates(
            plan=plan,
            total_days=total_days,
            subscription_count=subscription_count
        )
        for plan, total_days, subscription_count in rows
    ]
    
    # Total count without pagination/joins
    total = db.query(func.count(Plan.id)).filter(*filters).scalar()
    return PlansRepositoryResponse(plan_info=plan_aggregates, total=total)

def get_plan_by_id(db: Session, plan_id: UUID) -> Plan:
    try:   
        return db.query(Plan).filter(Plan.id == plan_id).first()
    except Exception as e:
        db.rollback()
        print(f"Error getting plan by id: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get plan by id: {str(e)}"
        )

def get_plan_by_id_and_created_by(db: Session, plan_id: UUID, created_by: str, is_admin: bool) -> Plan:
    try:
        if not is_admin:
            return db.query(Plan).filter(Plan.id == plan_id, Plan.created_by == created_by).first()
        else:
            return db.query(Plan).filter(Plan.id == plan_id).first()
    except Exception as e:
        db.rollback()
        print(f"Error getting plan by id and created by: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get plan by id and created by: {str(e)}"
        )

def get_plan_by_id_with_items_and_tasks(db: Session, plan_id: UUID) -> Plan:
    return db.query(Plan).filter(Plan.id == plan_id).options(joinedload(Plan.items), joinedload(Plan.tasks)).first()

def update_plan(db: Session, plan: Plan) -> Plan:

    try:
        db.add(plan)
        db.commit()
        db.refresh(plan)
        return plan
    except IntegrityError as e:
        db.rollback()
        print(f"Integrity error while updating plan: {e.orig}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update plan: {e.orig}"
        )
    except Exception as e:
        db.rollback()
        print(f"Error updating plan: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update plan: {str(e)}"
        )
