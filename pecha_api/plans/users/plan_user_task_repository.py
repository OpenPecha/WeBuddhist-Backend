from uuid import UUID
from sqlalchemy.orm import Session
from typing import List
from .plan_users_models import UserTaskCompletion
from pecha_api.plans.tasks.plan_tasks_models import PlanTask
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from starlette import status
from pecha_api.plans.auth.plan_auth_models import ResponseError
from pecha_api.plans.response_message import BAD_REQUEST


def save_user_task_completion(db: Session, user_task_completion: UserTaskCompletion):
    try:
        db.add(user_task_completion)
        db.commit()
        db.refresh(user_task_completion)
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ResponseError(error=BAD_REQUEST, message=str(e.orig)).model_dump())
    db.commit()
    db.refresh(user_task_completion)


def save_user_task_completions_bulk(db: Session, user_task_completions: List[UserTaskCompletion]) -> None:
    if not user_task_completions:
        return
    try:
        db.add_all(user_task_completions)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=ResponseError(error=BAD_REQUEST, message=str(e)).model_dump())


def get_user_task_completions_by_user_id_and_task_ids(db: Session, user_id: UUID, task_ids: List[UUID]) -> List[UserTaskCompletion]:
    return db.query(UserTaskCompletion).filter(UserTaskCompletion.user_id == user_id, UserTaskCompletion.task_id.in_(task_ids)).all()

def delete_user_task_completion(db: Session, user_id: UUID, task_id: UUID) -> None:
    db.query(UserTaskCompletion).filter(UserTaskCompletion.user_id == user_id, UserTaskCompletion.task_id == task_id).delete()
    db.commit()

def get_user_task_completion_by_user_id_and_task_id(db: Session, user_id: UUID, task_id: UUID) -> UserTaskCompletion:
    return db.query(UserTaskCompletion).filter(UserTaskCompletion.user_id == user_id, UserTaskCompletion.task_id == task_id).first()

def get_uncompleted_user_task_ids(db: Session, user_id: UUID, task_ids: List[UUID]) -> List[UUID]:
    rows = (
        db.query(PlanTask.id)
        .filter(
            PlanTask.id.in_(task_ids),
            ~db.query(UserTaskCompletion)
             .filter(
                 UserTaskCompletion.user_id == user_id,
                 UserTaskCompletion.task_id == PlanTask.id
             )
             .exists()
        )
        .all()
    )
    return [row[0] for row in rows]
