
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload
from .plan_items_models import PlanItem
from pecha_api.plans.tasks.plan_tasks_models import PlanTask
from pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_models import PlanSubTask
from fastapi import HTTPException
from starlette import status
from sqlalchemy import func, asc, update, bindparam
from uuid import UUID
from typing import List, Tuple
from pecha_api.plans.auth.plan_auth_models import ResponseError
from pecha_api.plans.response_message import BAD_REQUEST, PLAN_DAY_NOT_FOUND
from uuid import UUID
from .plan_items_response_models import ItemDayNumberDTO

def save_plan_items(db: Session, plan_items: List[PlanItem]):
    try:
        db.add_all(plan_items)
        db.commit()
        for item in plan_items:
            db.refresh(item)
        return plan_items
    except IntegrityError as e:
        db.rollback()
        print(f"Integrity error: {e.orig}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=ResponseError(error=BAD_REQUEST, 
            message=str(e.orig)).model_dump()
        )


def get_plan_item_by_id(db: Session, day_id: UUID) -> PlanItem:
    return db.query(PlanItem).filter(PlanItem.id == day_id).first()

def get_plan_item(db: Session, plan_id: UUID, day_id: UUID) -> PlanItem:
    plan_item = (
        db.query(PlanItem)
        .filter(PlanItem.id == day_id, PlanItem.plan_id == plan_id)
        .first()
    )
    if not plan_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=ResponseError(
                error=PLAN_DAY_NOT_FOUND, 
                message=PLAN_DAY_NOT_FOUND).model_dump()
            )
    return plan_item
def save_plan_item(db: Session, plan_item: PlanItem) -> PlanItem:
    try:
        db.add(plan_item)
        db.commit()
        db.refresh(plan_item)
        return plan_item
    except IntegrityError as e:
        db.rollback()
        print(f"Integrity error: {e.orig}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ResponseError(error=BAD_REQUEST, message=str(e.orig)).model_dump())

def get_plan_items_by_plan_id(db: Session, plan_id: UUID) -> List[PlanItem]:
    return (
        db.query(PlanItem)
        .filter(PlanItem.plan_id == plan_id)
        .order_by(asc(PlanItem.day_number))
        .all()
    )

def get_last_day_number(db: Session, plan_id: UUID) -> int:
    return db.query(func.max(PlanItem.day_number)).filter(PlanItem.plan_id == plan_id).scalar() or 0

def delete_plan_items(db: Session, plan_items: List[PlanItem]) -> None:
   
    try:
        for item in plan_items:
            db.delete(item)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Error deleting plan items: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ResponseError(
                error="DATABASE_ERROR",
                message="Failed to delete plan items"
            ).model_dump()
        )


def get_plan_day_with_tasks_and_subtasks(db: Session, plan_id: UUID, day_number: int) -> PlanItem:

    plan_item = (
        db.query(PlanItem)
        .options(
            joinedload(PlanItem.audio),
            joinedload(PlanItem.tasks).joinedload(PlanTask.sub_tasks).joinedload(PlanSubTask.timestamp),
        )
        .filter(PlanItem.plan_id == plan_id, PlanItem.day_number == day_number)
        .first()
    )

    if not plan_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=ResponseError(error=BAD_REQUEST, message=PLAN_DAY_NOT_FOUND).model_dump())
        
    return plan_item


def get_plan_day_by_id_with_tasks_and_subtasks(db: Session, plan_id: UUID, day_id: UUID) -> PlanItem:
    plan_item = (
        db.query(PlanItem)
        .options(
            joinedload(PlanItem.tasks).joinedload(PlanTask.sub_tasks).joinedload(PlanSubTask.timestamp),
        )
        .filter(PlanItem.plan_id == plan_id, PlanItem.id == day_id)
        .first()
    )

    if not plan_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ResponseError(error=BAD_REQUEST, message=PLAN_DAY_NOT_FOUND).model_dump(),
        )

    return plan_item


def get_day_by_plan_day_id(db: Session, plan_id: UUID, day_id: UUID) -> PlanItem:
    return db.query(PlanItem).filter(PlanItem.id == day_id, PlanItem.plan_id == plan_id).first()


def delete_day_by_id(db: Session, plan_id: UUID, day_id: UUID) -> None:
    try:
        db.query(PlanItem).filter(PlanItem.id == day_id, PlanItem.plan_id == plan_id).delete()
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=ResponseError(error=BAD_REQUEST, message=str(e)).model_dump())


def get_days_by_plan_id_and_day_ids(db: Session, plan_id: UUID, day_ids: List[UUID]) -> List[PlanItem]:
    if not day_ids:
        return []
    return (
        db.query(PlanItem)
        .filter(PlanItem.plan_id == plan_id, PlanItem.id.in_(day_ids))
        .all()
    )


def delete_days_by_ids(db: Session, plan_id: UUID, day_ids: List[UUID]) -> None:
    if not day_ids:
        return
    try:
        db.query(PlanItem).filter(
            PlanItem.id.in_(day_ids),
            PlanItem.plan_id == plan_id,
        ).delete(synchronize_session=False)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=ResponseError(error=BAD_REQUEST, message=str(e)).model_dump())


def get_days_by_plan_id(db: Session, plan_id: UUID) -> List[PlanItem]:
    return (
        db.query(PlanItem)
        .filter(PlanItem.plan_id == plan_id)
        .order_by(asc(PlanItem.day_number))
        .all()
    )

def get_days_by_day_ids(db: Session, day_ids: List[UUID]) -> List[PlanItem]:
    return db.query(PlanItem).filter(PlanItem.id.in_(day_ids)).order_by(asc(PlanItem.day_number)).all()

def update_day_by_id(db: Session, plan_id: UUID, day_id: UUID, day_number: int) -> None:
    try:
        db.query(PlanItem).filter(PlanItem.id == day_id, PlanItem.plan_id == plan_id).update({"day_number": day_number})
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=ResponseError(error=BAD_REQUEST, message=str(e)).model_dump())


def update_days_in_bulk_by_plan_id(db: Session, plan_id: UUID, days: List[ItemDayNumberDTO]) -> None:
    try:
        db.execute(
            update(PlanItem).where(PlanItem.plan_id == plan_id).execution_options(synchronize_session=False),
            days
        )
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=ResponseError(error=BAD_REQUEST, message=str(e)).model_dump())