from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from pecha_api.config import get_int

from .event_reminder_repository import (
    cancel_reminders_for_event,
    create_or_replace_reminder,
)

REMINDER_TYPE_T_MINUS_10 = "T_MINUS_10"
REMINDER_TYPE_T_ZERO = "T_ZERO"


def _minutes_before() -> int:
    return max(get_int("EVENT_REMINDER_MINUTES_BEFORE"), 1)


def schedule_event_reminders(db: Session, event_id: UUID, start_date: datetime) -> None:
    """Create the T-minus-N and at-start reminder rows for a newly created,
    non-recurring event. Reminders whose fire time has already passed are
    skipped rather than created, since they'd fire immediately anyway.

    Does not commit; the caller owns the transaction boundary so this can be
    composed atomically with the event write in the same session."""
    now = datetime.now(timezone.utc)
    t_minus_fire_at = start_date - timedelta(minutes=_minutes_before())

    if t_minus_fire_at > now:
        create_or_replace_reminder(db, event_id, REMINDER_TYPE_T_MINUS_10, t_minus_fire_at)
    if start_date > now:
        create_or_replace_reminder(db, event_id, REMINDER_TYPE_T_ZERO, start_date)


def reschedule_event_reminders(db: Session, event_id: UUID, new_start_date: datetime) -> None:
    """Recompute reminders after an event's start_date changes. Any
    undispatched rows are canceled first so a stale fire_at never survives
    the recompute.

    Does not commit; the caller owns the transaction boundary so this can be
    composed atomically with the event write in the same session."""
    cancel_reminders_for_event(db, event_id)
    schedule_event_reminders(db, event_id, new_start_date)


def cancel_event_reminders(db: Session, event_id: UUID) -> None:
    """Cancel any pending reminders, e.g. because the event was converted to
    a recurring event (out of scope for reminders) or deleted.

    Does not commit; the caller owns the transaction boundary so this can be
    composed atomically with the event write in the same session."""
    cancel_reminders_for_event(db, event_id)
