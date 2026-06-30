from fastapi import APIRouter, Depends
from starlette import status

from pecha_api.routines.routine_notifications.dependencies import verify_dispatch_token
from pecha_api.routines.routine_notifications.routine_notification_response_models import (
    RoutineNotificationTargetsResponse,
)
from pecha_api.routines.routine_notifications.routine_notification_service import (
    get_routine_notification_targets,
)

internal_routine_notifications_router = APIRouter(
    prefix="/internal",
    tags=["Internal"],
)


@internal_routine_notifications_router.get(
    "/routine-notification-targets",
    status_code=status.HTTP_200_OK,
)
def routine_notification_targets(
    _: None = Depends(verify_dispatch_token),
) -> RoutineNotificationTargetsResponse:
    return get_routine_notification_targets()
