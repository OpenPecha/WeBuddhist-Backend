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


def get_routine_by_id(db: Session, routine_id: UUID) -> Optional[Routine]:
    return (
        db.query(Routine)
        .filter(Routine.id == routine_id, Routine.deleted_at.is_(None))
        .first()
    )


def get_time_block_by_id(
    db: Session, time_block_id: UUID
) -> Optional[RoutineTimeBlock]:
    return (
        db.query(RoutineTimeBlock)
        .filter(
            RoutineTimeBlock.id == time_block_id,
            RoutineTimeBlock.deleted_at.is_(None),
        )
        .first()
    )


def get_existing_plan_source_ids_in_routine(
    db: Session, routine_id: UUID, exclude_time_block_id: Optional[UUID] = None
) -> List[UUID]:
    query = (
        db.query(RoutineSession.source_id)
        .join(RoutineTimeBlock, RoutineSession.time_block_id == RoutineTimeBlock.id)
        .filter(
            RoutineTimeBlock.routine_id == routine_id,
            RoutineTimeBlock.deleted_at.is_(None),
            RoutineSession.session_type == "PLAN",
        )
    )
    if exclude_time_block_id:
        query = query.filter(RoutineTimeBlock.id != exclude_time_block_id)
    return [row[0] for row in query.all()]


def check_duplicate_time_in_routine(
    db: Session,
    routine_id: UUID,
    time: str,
    exclude_time_block_id: Optional[UUID] = None,
) -> bool:
    query = db.query(RoutineTimeBlock).filter(
        RoutineTimeBlock.routine_id == routine_id,
        RoutineTimeBlock.time == time,
        RoutineTimeBlock.deleted_at.is_(None),
    )
    if exclude_time_block_id:
        query = query.filter(RoutineTimeBlock.id != exclude_time_block_id)
    return query.first() is not None


def delete_sessions_by_time_block_id(db: Session, time_block_id: UUID) -> None:
    db.query(RoutineSession).filter(
        RoutineSession.time_block_id == time_block_id
    ).delete()
    db.commit()


def update_time_block(
    db: Session,
    time_block: RoutineTimeBlock,
    time: str,
    time_int: int,
    notification_enabled: bool,
) -> RoutineTimeBlock:
    try:
        time_block.time = time
        time_block.time_int = time_int
        time_block.notification_enabled = notification_enabled
        db.commit()
        db.refresh(time_block)
        return time_block
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ResponseError(error=BAD_REQUEST, message=str(e.orig)).model_dump(),
        )
