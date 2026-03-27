from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from starlette import status
from uuid import UUID
from typing import Optional, List, Tuple

from pecha_api.plans.auth.plan_auth_models import ResponseError
from pecha_api.plans.response_message import BAD_REQUEST
from pecha_api.plans.plans_models import Plan
from .routines_models import Routine, RoutineTimeBlock, RoutineSession


def get_routine_by_user_id(
    db: Session, user_id: UUID, include_deleted: bool = False
) -> Optional[Routine]:

    query = db.query(Routine).filter(Routine.user_id == user_id)
    
    if not include_deleted:
        query = query.filter(Routine.deleted_at.is_(None))
    
    return query.first()


def get_plans_by_ids(db: Session, plan_ids: List[UUID]) -> List[Plan]:
    if not plan_ids:
        return []
    return db.query(Plan).filter(Plan.id.in_(plan_ids)).all()


def save_routine(db: Session, routine: Routine) -> Routine:
    try:
        db.add(routine)
        db.commit()
        db.refresh(routine)
        return routine
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ResponseError(error=BAD_REQUEST, message=str(e.orig)).model_dump(),
        )


def save_time_block(db: Session, time_block: RoutineTimeBlock) -> RoutineTimeBlock:
    try:
        db.add(time_block)
        db.commit()
        db.refresh(time_block)
        return time_block
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ResponseError(error=BAD_REQUEST, message=str(e.orig)).model_dump(),
        )


def save_sessions(db: Session, sessions: List[RoutineSession]) -> List[RoutineSession]:
    try:
        db.add_all(sessions)
        db.commit()
        for session in sessions:
            db.refresh(session)
        return sessions
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ResponseError(error=BAD_REQUEST, message=str(e.orig)).model_dump(),
        )


def get_time_blocks(db: Session,routine_id: UUID,include_deleted: bool = False,order_by_field=None,order_desc: bool = False,skip: int = 0,limit: int = 20) -> Tuple[List[RoutineTimeBlock], int]:

    query = db.query(RoutineTimeBlock).filter(RoutineTimeBlock.routine_id == routine_id)

    if not include_deleted:
        query = query.filter(RoutineTimeBlock.deleted_at.is_(None))

    if order_by_field is not None:
        query = query.order_by(order_by_field.desc() if order_desc else order_by_field)

    total = query.count()
    time_blocks = query.offset(skip).limit(limit).all()

    return time_blocks, total


def get_sessions_by_time_block_ids(db: Session, time_block_ids: List[UUID], order_by_field=None, order_desc: bool = False) -> List[RoutineSession]:
    if not time_block_ids:
        return []
    
    query = db.query(RoutineSession).filter(RoutineSession.time_block_id.in_(time_block_ids))
    
    if order_by_field is not None:
        query = query.order_by(order_by_field.desc() if order_desc else order_by_field)
    
    return query.all()
