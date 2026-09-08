import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from pecha_api.config import get_int
from pecha_api.db.database import SessionLocal
from pecha_api.events.event_repository import (
    list_undispatched_event_notifications,
    mark_event_notification_dispatched,
)
from pecha_api.events.notification_sqs_client import (
    build_event_notification_event_body,
    is_event_notification_sqs_configured,
    send_event_notification_message,
)

logger = logging.getLogger(__name__)


def enqueue_event_notification(event_id: UUID) -> str | None:
    """Enqueue an event notification. Never raises to callers.

    Returns the SQS MessageId on success, or None when the queue is not
    configured or enqueue fails. The event itself is already persisted.
    """
    if not is_event_notification_sqs_configured():
        logger.debug(
            "Skipping event notification enqueue for %s; SQS queue not configured",
            event_id,
        )
        return None

    try:
        sqs_message_id = send_event_notification_message(
            build_event_notification_event_body(event_id=str(event_id))
        )
    except Exception:
        logger.exception("Failed to enqueue event notification for event %s", event_id)
        return None

    try:
        with SessionLocal() as db:
            mark_event_notification_dispatched(
                db=db,
                event_id=event_id,
                sqs_message_id=sqs_message_id,
            )
    except Exception:
        logger.exception(
            "Enqueued event notification for %s but failed to persist SQS MessageId %s",
            event_id,
            sqs_message_id,
        )
    return sqs_message_id


def reconcile_undispatched_event_notifications() -> int:
    """Re-enqueue events that never recorded an SQS MessageId.

    Covers the commit-before-send crash window. Worker-side per-device
    idempotency makes duplicate queue events safe.
    """
    if not is_event_notification_sqs_configured():
        return 0

    grace_seconds = max(get_int("EVENT_NOTIFICATION_DISPATCH_RECONCILE_GRACE_SECONDS"), 1)
    batch_size = max(get_int("EVENT_NOTIFICATION_DISPATCH_RECONCILE_BATCH_SIZE"), 1)
    older_than = datetime.now(timezone.utc) - timedelta(seconds=grace_seconds)

    with SessionLocal() as db:
        events = list_undispatched_event_notifications(
            db=db,
            older_than=older_than,
            limit=batch_size,
        )
        event_ids = [event.id for event in events]

    requeued = 0
    for event_id in event_ids:
        if enqueue_event_notification(event_id):
            requeued += 1
            logger.info("Re-enqueued undispatched event notification for %s", event_id)

    return requeued
