from typing import List, Optional, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func, select
import _datetime
from _datetime import datetime, timezone

from pecha_api.accumulator import GroupAccumulator, GroupAccumulatorHistory, group_accumulator_joins
from pecha_api.users.users_models import Users


def _apply_created_at_range(query, range_start: datetime, range_end: datetime):
    return query.filter(
        GroupAccumulatorHistory.created_at >= range_start,
        GroupAccumulatorHistory.created_at <= range_end,
    )


def create_group_accumulator(
    db: Session,
    group_id: UUID,
    accumulator_id: Optional[UUID],
    title: Optional[str],
    image_key: Optional[str],
    target_count: Optional[int],
    start_date,
    end_date,
) -> GroupAccumulator:
    group_accumulator = GroupAccumulator(
        group_id=group_id,
        accumulator_id=accumulator_id,
        title=title,
        image_key=image_key,
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
    range_start: Optional[datetime] = None,
    range_end: Optional[datetime] = None,
) -> Tuple[List[GroupAccumulatorHistory], int]:
    query = db.query(GroupAccumulatorHistory).filter(
        GroupAccumulatorHistory.group_accumulator_id == group_accumulator_id
    )
    if range_start is not None and range_end is not None:
        query = _apply_created_at_range(query, range_start, range_end)
    total = query.count()
    history = query.order_by(GroupAccumulatorHistory.created_at.desc()).offset(skip).limit(limit).all()
    return history, total


def get_group_accumulator_count_in_range(
    db: Session,
    group_accumulator_id: UUID,
    range_start: datetime,
    range_end: datetime,
    user_id: Optional[UUID] = None,
) -> int:
    query = db.query(func.sum(GroupAccumulatorHistory.count)).filter(
        GroupAccumulatorHistory.group_accumulator_id == group_accumulator_id,
    )
    query = _apply_created_at_range(query, range_start, range_end)
    if user_id is not None:
        query = query.filter(GroupAccumulatorHistory.user_id == user_id)
    total = query.scalar()
    return int(total or 0)


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


def upsert_group_accumulator_join(
    db: Session,
    group_accumulator_id: UUID,
    user_id: UUID,
) -> None:
    exists_row = db.execute(
        select(group_accumulator_joins.c.group_accumulator_id).where(
            group_accumulator_joins.c.group_accumulator_id == group_accumulator_id,
            group_accumulator_joins.c.user_id == user_id,
        )
    ).first()
    if exists_row:
        return
    db.execute(
        group_accumulator_joins.insert().values(
            group_accumulator_id=group_accumulator_id,
            user_id=user_id,
            created_at=datetime.now(timezone.utc),
        )
    )
    db.commit()


def is_user_joined_group_accumulator(
    db: Session,
    group_accumulator_id: UUID,
    user_id: UUID,
) -> bool:
    row = db.execute(
        select(group_accumulator_joins.c.group_accumulator_id).where(
            group_accumulator_joins.c.group_accumulator_id == group_accumulator_id,
            group_accumulator_joins.c.user_id == user_id,
        )
    ).first()
    return row is not None


def get_group_accumulator_joiners_count(
    db: Session,
    group_accumulator_id: UUID,
) -> int:
    return (
        db.query(func.count())
        .select_from(group_accumulator_joins)
        .filter(group_accumulator_joins.c.group_accumulator_id == group_accumulator_id)
        .scalar()
        or 0
    )


def list_group_accumulator_joiners_paginated(
    db: Session,
    group_accumulator_id: UUID,
    skip: int,
    limit: int,
    range_start: datetime,
    range_end: datetime,
) -> Tuple[List[Tuple[Users, datetime, int, int]], int]:
    total_subq = (
        db.query(
            GroupAccumulatorHistory.user_id.label("user_id"),
            func.coalesce(func.sum(GroupAccumulatorHistory.count), 0).label("total_count"),
        )
        .filter(GroupAccumulatorHistory.group_accumulator_id == group_accumulator_id)
        .group_by(GroupAccumulatorHistory.user_id)
        .subquery()
    )
    today_subq = (
        db.query(
            GroupAccumulatorHistory.user_id.label("user_id"),
            func.coalesce(func.sum(GroupAccumulatorHistory.count), 0).label("today_count"),
        )
        .filter(GroupAccumulatorHistory.group_accumulator_id == group_accumulator_id)
        .filter(
            GroupAccumulatorHistory.created_at >= range_start,
            GroupAccumulatorHistory.created_at <= range_end,
        )
        .group_by(GroupAccumulatorHistory.user_id)
        .subquery()
    )
    query = (
        db.query(
            Users,
            group_accumulator_joins.c.created_at,
            func.coalesce(total_subq.c.total_count, 0).label("total_count"),
            func.coalesce(today_subq.c.today_count, 0).label("today_count"),
        )
        .join(
            group_accumulator_joins,
            Users.id == group_accumulator_joins.c.user_id,
        )
        .outerjoin(total_subq, Users.id == total_subq.c.user_id)
        .outerjoin(today_subq, Users.id == today_subq.c.user_id)
        .filter(group_accumulator_joins.c.group_accumulator_id == group_accumulator_id)
    )
    total = query.count()
    rows = (
        query.order_by(group_accumulator_joins.c.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [
        (user, joined_at, int(total_count or 0), int(today_count or 0))
        for user, joined_at, total_count, today_count in rows
    ], total
