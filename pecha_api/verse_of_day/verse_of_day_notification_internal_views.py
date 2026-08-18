from fastapi import APIRouter, Depends
from starlette import status

from pecha_api.routines.routine_notifications.dependencies import verify_dispatch_token
from pecha_api.verse_of_day.verse_of_day_notification_response_models import (
    VerseOfDayNotificationTargetsResponse,
)
from pecha_api.verse_of_day.verse_of_day_notification_service import (
    get_verse_of_day_notification_targets,
)

internal_verse_of_day_notifications_router = APIRouter(
    prefix="/internal",
    tags=["Internal"],
)


@internal_verse_of_day_notifications_router.get(
    "/verse-of-day-notification-targets",
    status_code=status.HTTP_200_OK,
)
def verse_of_day_notification_targets(
    _: None = Depends(verify_dispatch_token),
) -> VerseOfDayNotificationTargetsResponse:
    return get_verse_of_day_notification_targets()
