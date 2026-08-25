from uuid import UUID

from fastapi import APIRouter, Depends, Query
from starlette import status

from pecha_api.events.notification_response_models import EventNotificationTargetsResponse
from pecha_api.events.notification_service import get_event_notification_targets
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
