import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from pecha_api.config import get_int
from pecha_api.db.database import SessionLocal
from pecha_api.plans.groups.groups_repository import (
    list_undispatched_join_request_notifications,
    mark_join_request_notification_dispatched,
)
from pecha_api.plans.groups.join_request_sqs_client import (
    JOIN_REQUEST_CREATED_EVENT,
    JOIN_REQUEST_DECIDED_EVENT,
    build_join_request_event_body,
    is_join_request_notification_sqs_configured,
    send_join_request_notification_message,
)

logger = logging.getLogger(__name__)


def _enqueue(join_request_id: UUID, event_type: str, *, decision: bool) -> Optional[str]:
    """Never raises: the join request itself is already persisted."""
    if not is_join_request_notification_sqs_configured():
        logger.debug(
            "Skipping join request notification enqueue for %s; SQS queue not configured",
            join_request_id,
        )
        return None

    try:
        sqs_message_id = send_join_request_notification_message(
            build_join_request_event_body(
                join_request_id=str(join_request_id),
                event_type=event_type,
            )
        )
    except Exception:
        logger.exception(
            "Failed to enqueue %s notification for join request %s",
            event_type,
            join_request_id,
        )
        return None

    try:
        with SessionLocal() as db:
            mark_join_request_notification_dispatched(
                db=db,
                join_request_id=join_request_id,
                sqs_message_id=sqs_message_id,
                decision=decision,
            )
    except Exception:
        logger.exception(
            "Enqueued %s for join request %s but failed to persist SQS MessageId %s",
            event_type,
            join_request_id,
            sqs_message_id,
        )
    return sqs_message_id


def enqueue_join_request_created(join_request_id: UUID) -> Optional[str]:
    return _enqueue(join_request_id, JOIN_REQUEST_CREATED_EVENT, decision=False)


def enqueue_join_request_decided(join_request_id: UUID) -> Optional[str]:
    return _enqueue(join_request_id, JOIN_REQUEST_DECIDED_EVENT, decision=True)


def reconcile_undispatched_join_request_notifications() -> int:
    """Re-enqueue requests that never recorded an SQS MessageId.

    Covers the commit-before-send crash window; worker-side idempotency makes
    duplicate events safe."""
    if not is_join_request_notification_sqs_configured():
        return 0

    grace_seconds = max(
        get_int("JOIN_REQUEST_NOTIFICATION_DISPATCH_RECONCILE_GRACE_SECONDS"), 1
    )
    batch_size = max(get_int("JOIN_REQUEST_NOTIFICATION_DISPATCH_RECONCILE_BATCH_SIZE"), 1)
    older_than = datetime.now(timezone.utc) - timedelta(seconds=grace_seconds)

    with SessionLocal() as db:
        pending = list_undispatched_join_request_notifications(
            db=db,
            older_than=older_than,
            limit=batch_size,
        )
        join_request_ids = [item.id for item in pending]

    requeued = 0
    for join_request_id in join_request_ids:
        if enqueue_join_request_created(join_request_id):
            requeued += 1
            logger.info(
                "Re-enqueued undispatched join request notification for %s", join_request_id
            )
    return requeued
