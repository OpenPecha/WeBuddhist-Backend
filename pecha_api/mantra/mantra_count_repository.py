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


def _user_mantra_counts_query(db: Session, user_id: UUID):
    return (
        db.query(
            Accumulator.mantra_id.label("mantra_id"),
            func.coalesce(func.sum(Accumulator.current_count), 0).label("total_count"),
            func.max(Accumulator.updated_at).label("updated_at"),
        )
        .filter(
            Accumulator.user_id == user_id,
            Accumulator.deleted_at.is_(None),
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
