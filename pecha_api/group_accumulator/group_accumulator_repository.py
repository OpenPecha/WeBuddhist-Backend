from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func

from pecha_api.accumulator import GroupAccumulator, GroupAccumulatorHistory


def create_group_accumulator(
    db: Session,
    group_id: UUID,
    mantra_id: Optional[UUID],
    target_count: Optional[int],
    start_date,
    end_date,
) -> GroupAccumulator:
    group_accumulator = GroupAccumulator(
        group_id=group_id,
        mantra_id=mantra_id,
        target_count=target_count,
        start_date=start_date,
        end_date=end_date,
    )
    db.add(group_accumulator)
    db.commit()
    db.refresh(group_accumulator)
    return group_accumulator


def get_group_accumulators(
    db: Session,
    group_id: UUID,
    skip: int = 0,
    limit: int = 20,
) -> Tuple[List[GroupAccumulator], int]:
    query = db.query(GroupAccumulator).filter(GroupAccumulator.group_id == group_id)
    total = query.count()
    accumulators = query.order_by(GroupAccumulator.created_at.desc()).offset(skip).limit(limit).all()
    return accumulators, total


def get_group_accumulator_by_id(
    db: Session,
    group_accumulator_id: UUID,
) -> Optional[GroupAccumulator]:
    return db.query(GroupAccumulator).filter(GroupAccumulator.id == group_accumulator_id).first()


def update_group_accumulator(
    db: Session,
    group_accumulator: GroupAccumulator,
) -> GroupAccumulator:
    db.commit()
    db.refresh(group_accumulator)
    return group_accumulator


def delete_group_accumulator(
    db: Session,
    group_accumulator: GroupAccumulator,
) -> None:
    db.delete(group_accumulator)
    db.commit()


def add_group_history_row(
    db: Session,
    group_accumulator_id: UUID,
    user_id: UUID,
    count: int,
) -> GroupAccumulatorHistory:
    history = GroupAccumulatorHistory(
        group_accumulator_id=group_accumulator_id,
        user_id=user_id,
        count=count,
    )
    db.add(history)
    db.commit()
    db.refresh(history)
    return history


def get_group_accumulator_history(
    db: Session,
    group_accumulator_id: UUID,
    skip: int = 0,
    limit: int = 20,
) -> Tuple[List[GroupAccumulatorHistory], int]:
    query = db.query(GroupAccumulatorHistory).filter(
        GroupAccumulatorHistory.group_accumulator_id == group_accumulator_id
    )
    total = query.count()
    history = query.order_by(GroupAccumulatorHistory.created_at.desc()).offset(skip).limit(limit).all()
    return history, total


def get_group_accumulator_total_count(
    db: Session,
    group_accumulator_id: UUID,
) -> int:
    total = (
        db.query(func.sum(GroupAccumulatorHistory.count))
        .filter(GroupAccumulatorHistory.group_accumulator_id == group_accumulator_id)
        .scalar()
    )
    return total or 0


def verify_group_exists(db: Session, group_id: UUID) -> bool:
    from pecha_api.plans.groups.groups_models import AuthorGroup
    return db.query(AuthorGroup).filter(AuthorGroup.id == group_id).first() is not None
