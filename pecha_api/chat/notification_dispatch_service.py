import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from pecha_api.chat.repository import (
    list_undispatched_chat_notification_messages,
    mark_message_notification_dispatched,
)
from pecha_api.chat.sqs_client import (
    build_chat_notification_event_body,
    is_chat_notification_sqs_configured,
    send_chat_notification_message,
)
from pecha_api.config import get_int
from pecha_api.db.database import SessionLocal

logger = logging.getLogger(__name__)


def enqueue_chat_message_notification(message_id: UUID) -> str | None:
    """Enqueue a chat message notification event. Never raises to callers.

    Returns the SQS MessageId on success, or None when the queue is not
    configured or enqueue fails. The chat message itself is already persisted.
    """
    if not is_chat_notification_sqs_configured():
        logger.debug(
            "Skipping chat notification enqueue for %s; SQS queue not configured",
            message_id,
        )
        return None

    try:
        sqs_message_id = send_chat_notification_message(
            build_chat_notification_event_body(message_id=str(message_id))
        )
    except Exception:
        logger.exception("Failed to enqueue chat notification for message %s", message_id)
        return None

    try:
        with SessionLocal() as db:
            mark_message_notification_dispatched(
                db=db,
                message_id=message_id,
                sqs_message_id=sqs_message_id,
            )
    except Exception:
        logger.exception(
            "Enqueued chat notification for %s but failed to persist SQS MessageId %s",
            message_id,
            sqs_message_id,
        )
    return sqs_message_id


def reconcile_undispatched_chat_notifications() -> int:
    """Re-enqueue chat messages that never recorded an SQS MessageId.

    Covers the commit-before-send crash window. Worker-side per-device
    idempotency makes duplicate queue events safe.
    """
    if not is_chat_notification_sqs_configured():
        return 0

    grace_seconds = max(get_int("CHAT_NOTIFICATION_DISPATCH_RECONCILE_GRACE_SECONDS"), 1)
    batch_size = max(get_int("CHAT_NOTIFICATION_DISPATCH_RECONCILE_BATCH_SIZE"), 1)
    older_than = datetime.now(timezone.utc) - timedelta(seconds=grace_seconds)

    with SessionLocal() as db:
        messages = list_undispatched_chat_notification_messages(
            db=db,
            older_than=older_than,
            limit=batch_size,
        )
        message_ids = [message.id for message in messages]

    requeued = 0
    for message_id in message_ids:
        if enqueue_chat_message_notification(message_id):
            requeued += 1
            logger.info("Re-enqueued undispatched chat notification for %s", message_id)

    return requeued
