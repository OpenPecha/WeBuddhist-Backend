from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from pecha_api.users.users_models import Users

from .event_participant_model import GroupEventParticipant


def is_user_joined_event(db: Session, event_id: UUID, user_id: UUID) -> bool:
    row = db.execute(
        select(GroupEventParticipant.id).where(
            GroupEventParticipant.event_id == event_id,
            GroupEventParticipant.user_id == user_id,
        )
    ).first()
    return row is not None


def get_joined_event_ids_by_user(
    db: Session,
    user_id: UUID,
    event_ids: Optional[List[UUID]] = None,
) -> List[UUID]:
    if event_ids is not None and not event_ids:
        return []
    query = db.query(GroupEventParticipant.event_id).filter(
        GroupEventParticipant.user_id == user_id,
    )
    if event_ids is not None:
        query = query.filter(GroupEventParticipant.event_id.in_(event_ids))
    return [row.event_id for row in query.all()]


def upsert_event_participant(db: Session, event_id: UUID, user_id: UUID) -> None:
    """Join an event. Idempotent: joining again is a no-op."""
    if is_user_joined_event(db=db, event_id=event_id, user_id=user_id):
        return
    try:
        db.add(
            GroupEventParticipant(
                event_id=event_id,
                user_id=user_id,
                created_at=datetime.now(timezone.utc),
            )
        )
        db.commit()
    except IntegrityError:
        # Concurrent join won the race; the unique constraint already
        # guarantees a single row, so treat this as already joined.
        db.rollback()


def remove_event_participant(db: Session, event_id: UUID, user_id: UUID) -> bool:
    """Leave an event. Returns True when a row was actually removed."""
    participant = (
        db.query(GroupEventParticipant)
        .filter(
            GroupEventParticipant.event_id == event_id,
            GroupEventParticipant.user_id == user_id,
        )
        .first()
    )
    if participant is None:
        return False
    db.delete(participant)
    db.commit()
    return True


def get_event_participants_paginated(
    db: Session,
    event_id: UUID,
    skip: int = 0,
    limit: int = 20,
) -> Tuple[List[Tuple[Users, datetime]], int]:
    query = (
        db.query(Users, GroupEventParticipant.created_at)
        .join(GroupEventParticipant, GroupEventParticipant.user_id == Users.id)
        .filter(GroupEventParticipant.event_id == event_id)
    )
    total = query.count()
    rows = (
        query.order_by(GroupEventParticipant.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [(user, created_at) for user, created_at in rows], total


def get_event_participant_count(db: Session, event_id: UUID) -> int:
    return (
        db.query(func.count(GroupEventParticipant.id))
        .filter(GroupEventParticipant.event_id == event_id)
        .scalar()
        or 0
    )


def get_event_participant_counts(
    db: Session,
    event_ids: List[UUID],
) -> Dict[UUID, int]:
    if not event_ids:
        return {}
    rows = (
        db.query(
            GroupEventParticipant.event_id,
            func.count(GroupEventParticipant.id).label("participant_count"),
        )
        .filter(GroupEventParticipant.event_id.in_(event_ids))
        .group_by(GroupEventParticipant.event_id)
        .all()
    )
    return {row.event_id: int(row.participant_count) for row in rows}
