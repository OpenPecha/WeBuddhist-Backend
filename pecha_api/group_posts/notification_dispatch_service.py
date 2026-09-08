import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from pecha_api.config import get_int
from pecha_api.db.database import SessionLocal
from pecha_api.group_posts.notification_sqs_client import (
    build_group_post_notification_event_body,
    is_group_post_notification_sqs_configured,
    send_group_post_notification_message,
)
from pecha_api.group_posts.repository import (
    list_undispatched_group_post_notifications,
    mark_post_notification_dispatched,
)

logger = logging.getLogger(__name__)


def enqueue_group_post_notification(post_id: UUID) -> str | None:
    """Enqueue a group post notification event. Never raises to callers.

    Returns the SQS MessageId on success, or None when the queue is not
    configured or enqueue fails. The post itself is already persisted.
    """
    if not is_group_post_notification_sqs_configured():
        logger.debug(
            "Skipping group post notification enqueue for %s; SQS queue not configured",
            post_id,
        )
        return None

    try:
        sqs_message_id = send_group_post_notification_message(
            build_group_post_notification_event_body(post_id=str(post_id))
        )
    except Exception:
        logger.exception("Failed to enqueue group post notification for post %s", post_id)
        return None

    try:
        with SessionLocal() as db:
            mark_post_notification_dispatched(
                db=db,
                post_id=post_id,
                sqs_message_id=sqs_message_id,
            )
    except Exception:
        logger.exception(
            "Enqueued group post notification for %s but failed to persist SQS MessageId %s",
            post_id,
            sqs_message_id,
        )
    return sqs_message_id


def reconcile_undispatched_group_post_notifications() -> int:
    """Re-enqueue group posts that never recorded an SQS MessageId.

    Covers the commit-before-send crash window. Worker-side per-device
    idempotency makes duplicate queue events safe.
    """
    if not is_group_post_notification_sqs_configured():
        return 0

    grace_seconds = max(get_int("GROUP_POST_NOTIFICATION_DISPATCH_RECONCILE_GRACE_SECONDS"), 1)
    batch_size = max(get_int("GROUP_POST_NOTIFICATION_DISPATCH_RECONCILE_BATCH_SIZE"), 1)
    older_than = datetime.now(timezone.utc) - timedelta(seconds=grace_seconds)

    with SessionLocal() as db:
        posts = list_undispatched_group_post_notifications(
            db=db,
            older_than=older_than,
            limit=batch_size,
        )
        post_ids = [post.id for post in posts]

    requeued = 0
    for post_id in post_ids:
        if enqueue_group_post_notification(post_id):
            requeued += 1
            logger.info("Re-enqueued undispatched group post notification for %s", post_id)

    return requeued
