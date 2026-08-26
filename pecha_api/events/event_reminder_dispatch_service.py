import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from pecha_api.config import get_int
from pecha_api.db.database import SessionLocal

from .event_reminder_repository import (
    claim_reminder_for_dispatch,
    list_due_reminders,
    list_undispatched_reminders_missing_sqs_id,
    mark_reminder_sqs_message_id,
)
from .notification_sqs_client import (
    build_event_reminder_event_body,
    is_event_notification_sqs_configured,
    send_event_notification_message,
)

logger = logging.getLogger(__name__)


def _send_reminder(reminder_id: UUID, event_id: UUID, reminder_type: str) -> str | None:
    try:
        sqs_message_id = send_event_notification_message(
            build_event_reminder_event_body(event_id=str(event_id), reminder_type=reminder_type)
        )
    except Exception:
        logger.exception(
            "Failed to enqueue event reminder %s (%s) for event %s",
            reminder_id, reminder_type, event_id,
        )
        return None

    try:
        with SessionLocal() as db:
            mark_reminder_sqs_message_id(db, reminder_id, sqs_message_id)
    except Exception:
        logger.exception(
            "Enqueued event reminder %s but failed to persist SQS MessageId %s",
            reminder_id, sqs_message_id,
        )
    return sqs_message_id


def dispatch_due_event_reminders() -> int:
    """Poll for reminders whose fire_at has passed and enqueue them.

    Rows are claimed optimistically (dispatched_at stamped) before the SQS
    send so overlapping poll cycles across replicas don't double-enqueue;
    worker-side per-device idempotency remains the correctness backstop.
    """
    if not is_event_notification_sqs_configured():
        return 0

    batch_size = max(get_int("EVENT_REMINDER_DISPATCH_BATCH_SIZE"), 1)
    now = datetime.now(timezone.utc)

    with SessionLocal() as db:
        due = list_due_reminders(db, now=now, limit=batch_size)
        candidates = [(reminder.id, reminder.event_id, reminder.reminder_type) for reminder in due]

    dispatched = 0
    for reminder_id, event_id, reminder_type in candidates:
        with SessionLocal() as db:
            claimed = claim_reminder_for_dispatch(db, reminder_id)
        if not claimed:
            continue
        if _send_reminder(reminder_id, event_id, reminder_type):
            dispatched += 1
            logger.info("Dispatched event reminder %s (%s) for event %s", reminder_id, reminder_type, event_id)

    return dispatched


def reconcile_undispatched_event_reminders() -> int:
    """Re-send reminders that were claimed but never recorded an SQS
    MessageId, covering the commit-before-send crash window."""
    if not is_event_notification_sqs_configured():
        return 0

    grace_seconds = max(get_int("EVENT_REMINDER_DISPATCH_RECONCILE_GRACE_SECONDS"), 1)
    batch_size = max(get_int("EVENT_REMINDER_DISPATCH_RECONCILE_BATCH_SIZE"), 1)
    older_than = datetime.now(timezone.utc) - timedelta(seconds=grace_seconds)

    with SessionLocal() as db:
        stuck = list_undispatched_reminders_missing_sqs_id(db, older_than=older_than, limit=batch_size)
        candidates = [(reminder.id, reminder.event_id, reminder.reminder_type) for reminder in stuck]

    requeued = 0
    for reminder_id, event_id, reminder_type in candidates:
        if _send_reminder(reminder_id, event_id, reminder_type):
            requeued += 1
            logger.info("Re-enqueued undispatched event reminder %s for event %s", reminder_id, event_id)

    return requeued
