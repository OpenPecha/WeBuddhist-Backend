from sqlalchemy.orm import Session
from typing import List, Tuple
from uuid import UUID
from .timer_model import Timer


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
