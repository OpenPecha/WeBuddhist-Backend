from datetime import datetime
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from pecha_api.accumulator.accumulator_models import Accumulator


class UserMantraCountRow:
    def __init__(
        self,
        mantra_id: UUID,
        total_count: int,
        updated_at: Optional[datetime],
    ):
        self.mantra_id = mantra_id
        self.total_count = total_count
        self.updated_at = updated_at


class GroupMantraCountRow:
    def __init__(
        self,
        mantra_id: UUID,
        total_count: int,
    ):
        self.mantra_id = mantra_id
        self.total_count = total_count


def _user_mantra_counts_query(db: Session, user_id: UUID):
    return (
        db.query(
            Accumulator.mantra_id.label("mantra_id"),
            func.coalesce(func.sum(Accumulator.current_count), 0).label("total_count"),
            func.max(Accumulator.updated_at).label("updated_at"),
        )
        .filter(
            Accumulator.user_id == user_id,
            Accumulator.mantra_id.isnot(None),
        )
        .group_by(Accumulator.mantra_id)
    )


def get_user_mantra_counts(
    db: Session,
    user_id: UUID,
    skip: int = 0,
    limit: int = 20,
) -> Tuple[List[UserMantraCountRow], int]:
    grouped = _user_mantra_counts_query(db, user_id).subquery()
    total = db.query(func.count()).select_from(grouped).scalar() or 0

    rows = (
        db.query(grouped)
        .order_by(grouped.c.updated_at.desc().nullslast())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return [
        UserMantraCountRow(
            mantra_id=row.mantra_id,
            total_count=int(row.total_count or 0),
            updated_at=row.updated_at,
        )
        for row in rows
    ], total


def get_user_mantra_count_for_mantra(
    db: Session,
    user_id: UUID,
    mantra_id: UUID,
) -> Tuple[int, Optional[datetime]]:
    row = (
        _user_mantra_counts_query(db, user_id)
        .filter(Accumulator.mantra_id == mantra_id)
        .first()
    )
    if row is None:
        return 0, None
    return int(row.total_count or 0), row.updated_at


def get_group_mantra_accumulations(
    db: Session,
    group_id: UUID,
    skip: int = 0,
    limit: int = 20,
) -> Tuple[List[GroupMantraCountRow], int, int]:
    """
    Returns: (rows, total_mantra_count, grand_total_count)
    - rows: paginated list of mantras with their counts
    - total_mantra_count: total number of distinct mantras
    - grand_total_count: sum of all mantra counts for the group
    """
    grouped = (
        db.query(
            Accumulator.mantra_id.label("mantra_id"),
            func.coalesce(func.sum(Accumulator.current_count), 0).label("total_count"),
        )
        .filter(
            Accumulator.group_id == group_id,
            Accumulator.mantra_id.isnot(None),
            Accumulator.current_count > 0,
        )
        .group_by(Accumulator.mantra_id)
        .subquery()
    )
    
    total_mantra_count = db.query(func.count()).select_from(grouped).scalar() or 0
    grand_total_count = db.query(func.coalesce(func.sum(grouped.c.total_count), 0)).scalar() or 0
    
    rows = (
        db.query(grouped)
        .order_by(grouped.c.total_count.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    return [
        GroupMantraCountRow(
            mantra_id=row.mantra_id,
            total_count=int(row.total_count or 0),
        )
        for row in rows
    ], total_mantra_count, int(grand_total_count)
