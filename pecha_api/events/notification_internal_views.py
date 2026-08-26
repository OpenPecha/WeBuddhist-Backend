from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from starlette import status

from pecha_api.config import get_int
from pecha_api.events.event_reminder_service import REMINDER_TYPE_T_MINUS_10, REMINDER_TYPE_T_ZERO
from pecha_api.events.notification_response_models import (
    EventNotificationTargetsResponse,
    EventReminderTargetsResponse,
)
from pecha_api.events.notification_service import get_event_notification_targets
from pecha_api.events.reminder_notification_service import get_event_reminder_targets
from pecha_api.routines.routine_notifications.dependencies import verify_dispatch_token

internal_event_notifications_router = APIRouter(
    prefix="/internal",
    tags=["Internal"],
)


@internal_event_notifications_router.get(
    "/event-notification-targets/{event_id}",
    status_code=status.HTTP_200_OK,
)
def event_notification_targets(
    event_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    _: None = Depends(verify_dispatch_token),
) -> EventNotificationTargetsResponse:
    return get_event_notification_targets(event_id=event_id, skip=skip, limit=limit)


@internal_event_notifications_router.get(
    "/event-reminder-targets/{event_id}",
    status_code=status.HTTP_200_OK,
)
def event_reminder_targets(
    event_id: UUID,
    reminder_type: Literal[REMINDER_TYPE_T_MINUS_10, REMINDER_TYPE_T_ZERO] = Query(...),
    fire_at: Optional[datetime] = Query(
        None,
        description=(
            "The exact fire_at this dispatch was queued for. Used to detect "
            "a message that outlived a cancel/reschedule of the same "
            "reminder and was superseded by a later dispatch before it was "
            "processed."
        ),
    ),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    _: None = Depends(verify_dispatch_token),
) -> EventReminderTargetsResponse:
    return get_event_reminder_targets(
        event_id=event_id,
        reminder_type=reminder_type,
        minutes_before=max(get_int("EVENT_REMINDER_MINUTES_BEFORE"), 1),
        skip=skip,
        limit=limit,
        fire_at=fire_at,
    )
