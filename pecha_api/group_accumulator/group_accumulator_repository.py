from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func
import _datetime
from _datetime import datetime

from pecha_api.accumulator import GroupAccumulator, GroupAccumulatorHistory


def create_group_accumulator(
    db: Session,
    group_id: UUID,
    accumulator_id: Optional[UUID],
    title: Optional[str],
    target_count: Optional[int],
    start_date,
    end_date,
) -> GroupAccumulator:
    group_accumulator = GroupAccumulator(
        group_id=group_id,
        accumulator_id=accumulator_id,
        title=title,
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
    query = db.query(GroupAccumulator).filter(
        GroupAccumulator.group_id == group_id,
        GroupAccumulator.deleted_at.is_(None)
    )
    total = query.count()
    accumulators = query.order_by(GroupAccumulator.created_at.desc()).offset(skip).limit(limit).all()
    return accumulators, total


def get_group_accumulator_by_id(
    db: Session,
    group_accumulator_id: UUID,
) -> Optional[GroupAccumulator]:
    return db.query(GroupAccumulator).filter(
        GroupAccumulator.id == group_accumulator_id,
        GroupAccumulator.deleted_at.is_(None)
    ).first()


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
    """Soft-delete: mark deleted_at so the group accumulator drops out of active
    lists while its history rows are preserved."""
    group_accumulator.deleted_at = datetime.now(_datetime.timezone.utc)
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


def get_user_group_accumulator_count(
    db: Session,
    group_accumulator_id: UUID,
    user_id: UUID,
) -> int:
    """Get a specific user's current count for a group accumulator by summing their history rows."""
    total = (
        db.query(func.sum(GroupAccumulatorHistory.count))
        .filter(
            GroupAccumulatorHistory.group_accumulator_id == group_accumulator_id,
            GroupAccumulatorHistory.user_id == user_id
        )
        .scalar()
    )
    return total or 0


def verify_group_exists(db: Session, group_id: UUID) -> bool:
    from pecha_api.plans.groups.groups_models import AuthorGroup
    return db.query(AuthorGroup).filter(AuthorGroup.id == group_id).first() is not None


class GroupAccumulatorMemberRow:
    def __init__(self, user_id: UUID, total_count: int):
        self.user_id = user_id
        self.total_count = total_count


def get_group_accumulator_member_contributions(
    db: Session,
    group_accumulator_id: UUID,
    skip: int = 0,
    limit: int = 20,
) -> Tuple[List[GroupAccumulatorMemberRow], int]:
    """
    Get member contributions for a specific group accumulator.
    Returns: (rows, total_member_count)
    """
    grouped = (
        db.query(
            GroupAccumulatorHistory.user_id.label("user_id"),
            func.coalesce(func.sum(GroupAccumulatorHistory.count), 0).label("total_count"),
        )
        .filter(
            GroupAccumulatorHistory.group_accumulator_id == group_accumulator_id,
            GroupAccumulatorHistory.count > 0,
        )
        .group_by(GroupAccumulatorHistory.user_id)
        .subquery()
    )
    
    total_member_count = db.query(func.count()).select_from(grouped).scalar() or 0
    
    rows = (
        db.query(grouped)
        .order_by(grouped.c.total_count.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    return [
        GroupAccumulatorMemberRow(
            user_id=row.user_id,
            total_count=int(row.total_count or 0),
        )
        for row in rows
    ], total_member_count
