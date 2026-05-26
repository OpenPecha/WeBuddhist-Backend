from uuid import UUID
from sqlalchemy import select, update, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from fastapi import HTTPException
from starlette import status
from typing import List, Optional
from sqlalchemy import asc


from pecha_api.db.database import SessionLocal
from pecha_api.plans.items.plan_items_repository import get_plan_item
from pecha_api.plans.tasks.plan_tasks_models import PlanTask
from pecha_api.plans.tasks.plan_tasks_response_model import CreateTaskRequest, TaskDTO, TaskOrderItem
from pecha_api.plans.auth.plan_auth_models import ResponseError
from pecha_api.plans.response_message import BAD_REQUEST, TASK_NOT_FOUND 


def save_task(db: Session, new_task: PlanTask):
    try:
        db.add(new_task)
        db.commit()
        db.refresh(new_task)
        return new_task
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=ResponseError(error=BAD_REQUEST, message=str(e.orig)).model_dump())

def get_tasks_by_item_ids(db: Session, plan_item_ids: List[UUID]) -> List[PlanTask]:
    if not plan_item_ids:
        return {}

    tasks = (
        db.query(PlanTask)
        .filter(PlanTask.plan_item_id.in_(plan_item_ids))
        .order_by(asc(PlanTask.plan_item_id), asc(PlanTask.display_order))
        .all()
    )

    return tasks

def get_task_by_id(db: Session, task_id: UUID) -> PlanTask:
    from pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_models import PlanSubTask

    task = (
        db.query(PlanTask)
        .options(joinedload(PlanTask.sub_tasks).joinedload(PlanSubTask.timestamp))
        .filter(PlanTask.id == task_id)
        .first()
    )
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ResponseError(error=BAD_REQUEST, message=TASK_NOT_FOUND).model_dump())
    return task



def delete_task(db: Session, task_id: UUID):
    task = get_task_by_id(db=db, task_id=task_id)
    try:
        db.delete(task)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=ResponseError(error=BAD_REQUEST, message=str(e)).model_dump())
    return db.query(PlanTask).filter(PlanTask.id == task_id).first()

def update_task_day(db: Session, updated_task: PlanTask) -> PlanTask:
    db.commit()
    db.refresh(updated_task)
    return updated_task

def update_task_title(db: Session, updated_task: PlanTask) -> PlanTask:
    db.commit()
    db.refresh(updated_task)
    return updated_task

def get_tasks_by_plan_item_id(db: Session, plan_item_id: UUID) -> List[PlanTask]:
    return (db.query(PlanTask)
        .filter(PlanTask.plan_item_id == plan_item_id)
        .order_by(PlanTask.display_order)
        .all()
    )


def reorder_day_tasks_display_order(db: Session, tasks: List[PlanTask]):
    try:
        for task in tasks:
            db.commit()
            db.refresh(task)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=ResponseError(error=BAD_REQUEST, message=str(e)).model_dump())

def update_task_order(db: Session, day_id: UUID, update_task_orders: List[TaskOrderItem]) -> None:
    try:
        db.execute(
            update(PlanTask).where(PlanTask.plan_item_id == day_id).execution_options(synchronize_session=False),
            update_task_orders
        )
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=ResponseError(error=BAD_REQUEST, message=str(e)).model_dump())



def get_task_by_display_order(db: Session, plan_item_id: UUID, display_order: int) -> PlanTask:
    task = (
        db.query(PlanTask)
        .filter(
            PlanTask.plan_item_id == plan_item_id,
            PlanTask.display_order == display_order
        )
        .first()
    )
    return task

def get_tasks_by_plan_item_id(db: Session, plan_item_id: UUID) -> List[PlanTask]:
    tasks = (
        db.query(PlanTask)
        .filter(PlanTask.plan_item_id == plan_item_id)
        .order_by(asc(PlanTask.display_order))
        .all()
    )
    return tasks

