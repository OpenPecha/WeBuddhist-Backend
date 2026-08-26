from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from .event_reminder_model import EventReminder


def create_or_replace_reminder(
    db: Session,
    event_id: UUID,
    reminder_type: str,
    fire_at: datetime,
) -> None:
    """Upsert a reminder row for (event_id, reminder_type), resetting its
    dispatch/cancel state so a rescheduled event gets a fresh reminder. Does
    not commit; callers own the transaction boundary so this can be composed
    atomically with other writes in the same session."""
    now = datetime.now(timezone.utc)
    stmt = insert(EventReminder).values(
        event_id=event_id,
        reminder_type=reminder_type,
        fire_at=fire_at,
        sqs_message_id=None,
        dispatched_at=None,
        canceled_at=None,
        created_at=now,
    )
    stmt = stmt.on_conflict_do_update(
        constraint="uq_event_reminders_event_type",
        set_={
            "fire_at": fire_at,
            "sqs_message_id": None,
            "dispatched_at": None,
            "canceled_at": None,
        },
    )
    db.execute(stmt)


def cancel_reminders_for_event(db: Session, event_id: UUID) -> None:
    """Marks every not-yet-canceled reminder row for the event as canceled,
    including one a concurrent dispatcher may have just claimed (stamped
    dispatched_at) but not yet sent - that in-flight claim still needs a
    signal to skip the send, which the caller checks via get_reminder_by_id
    right before dispatching. Does not commit; callers own the transaction
    boundary so this can be composed atomically with other writes in the
    same session."""
    db.query(EventReminder).filter(
        EventReminder.event_id == event_id,
        EventReminder.canceled_at.is_(None),
    ).update(
        {EventReminder.canceled_at: datetime.now(timezone.utc)},
        synchronize_session=False,
    )


def list_due_reminders(db: Session, *, now: datetime, limit: int) -> List[EventReminder]:
    return (
        db.query(EventReminder)
        .filter(
            EventReminder.fire_at <= now,
            EventReminder.dispatched_at.is_(None),
            EventReminder.canceled_at.is_(None),
        )
        .order_by(EventReminder.fire_at.asc())
        .limit(limit)
        .all()
    )


def claim_reminder_for_dispatch(db: Session, reminder_id: UUID) -> bool:
    """Optimistically claim a reminder by stamping dispatched_at before the
    SQS send, so overlapping pollers don't double-enqueue. Returns True if
    this call won the claim."""
    now = datetime.now(timezone.utc)
    result = db.query(EventReminder).filter(
        EventReminder.id == reminder_id,
        EventReminder.dispatched_at.is_(None),
        EventReminder.canceled_at.is_(None),
    ).update({EventReminder.dispatched_at: now}, synchronize_session=False)
    db.commit()
    return result == 1


def mark_reminder_sqs_message_id(db: Session, reminder_id: UUID, sqs_message_id: str) -> None:
    db.query(EventReminder).filter(EventReminder.id == reminder_id).update(
        {EventReminder.sqs_message_id: sqs_message_id},
        synchronize_session=False,
    )
    db.commit()


def list_undispatched_reminders_missing_sqs_id(
    db: Session,
    *,
    older_than: datetime,
    limit: int,
) -> List[EventReminder]:
    """Reminders that were claimed (dispatched_at set) but never recorded an
    SQS MessageId - the commit-before-send crash window."""
    return (
        db.query(EventReminder)
        .filter(
            EventReminder.dispatched_at.isnot(None),
            EventReminder.dispatched_at <= older_than,
            EventReminder.sqs_message_id.is_(None),
            EventReminder.canceled_at.is_(None),
        )
        .order_by(EventReminder.dispatched_at.asc())
        .limit(limit)
        .all()
    )


def get_event_reminder(db: Session, event_id: UUID, reminder_type: str) -> Optional[EventReminder]:
    return (
        db.query(EventReminder)
        .filter(
            EventReminder.event_id == event_id,
            EventReminder.reminder_type == reminder_type,
        )
        .first()
    )


def get_reminder_by_id(db: Session, reminder_id: UUID) -> Optional[EventReminder]:
    return db.query(EventReminder).filter(EventReminder.id == reminder_id).first()
