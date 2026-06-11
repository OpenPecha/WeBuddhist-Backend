from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Tuple, Optional
from uuid import UUID
from fastapi import HTTPException
from starlette import status
from .timer_model import Timer


def save_timer(db: Session, timer: Timer) -> Timer:
    try:
        db.add(timer)
        db.commit()
        db.refresh(timer)
        return timer
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "BAD_REQUEST", "message": str(e.orig)}
        )


def get_timer_by_id(db: Session, timer_id: UUID) -> Optional[Timer]:
    return db.query(Timer).filter(Timer.id == timer_id).first()


def update_timer(db: Session, timer: Timer) -> Timer:
    try:
        db.commit()
        db.refresh(timer)
        return timer
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "BAD_REQUEST", "message": str(e.orig)}
        )


def delete_timer(db: Session, timer: Timer) -> None:
    try:
        db.delete(timer)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "BAD_REQUEST", "message": str(e)}
        )


def get_timers_by_group(
    db: Session,
    group_id: UUID,
    skip: int = 0,
    limit: int = 20
) -> Tuple[List[Timer], int]:

    query = db.query(Timer).filter(Timer.group_id == group_id)
    
    total = query.count()
    timers = query.order_by(Timer.created_at.desc()).offset(skip).limit(limit).all()
    
    return timers, total


def get_user_timers_by_group(
    db: Session,
    user_id: UUID,
    group_id: UUID,
    skip: int = 0,
    limit: int = 20
) -> Tuple[List[Timer], int]:

    query = db.query(Timer).filter(
        Timer.user_id == user_id,
        Timer.group_id == group_id
    )
    
    total = query.count()
    timers = query.order_by(Timer.created_at.desc()).offset(skip).limit(limit).all()
    
    return timers, total
