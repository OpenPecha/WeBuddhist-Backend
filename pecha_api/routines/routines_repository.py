from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from starlette import status
from uuid import UUID
from typing import Optional, List

from pecha_api.plans.auth.plan_auth_models import ResponseError
from pecha_api.plans.response_message import BAD_REQUEST
from pecha_api.plans.plans_models import Plan
from .routines_models import Routine, RoutineTimeBlock, RoutineSession


def get_routine_by_user_id(db: Session, user_id: UUID) -> Optional[Routine]:
    return (
        db.query(Routine)
        .filter(Routine.user_id == user_id, Routine.deleted_at.is_(None))
        .first()
    )


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
