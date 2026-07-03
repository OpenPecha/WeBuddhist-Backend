from uuid import UUID

from fastapi import APIRouter, Depends, Query
from starlette import status

from pecha_api.routines.routine_notifications.dependencies import verify_dispatch_token
from pecha_api.routines.routine_notifications.routine_notification_response_models import (
    NotificationContentDTO,
    RoutineNotificationTargetsResponse,
)
from pecha_api.routines.routine_notifications.routine_notification_service import (
    get_routine_notification_targets,
    resolve_plan_notification_content,
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


@internal_routine_notifications_router.get(
    "/plan-notification-content",
    status_code=status.HTTP_200_OK,
)
def plan_notification_content(
    user_id: UUID = Query(...),
    plan_id: UUID = Query(...),
    _: None = Depends(verify_dispatch_token),
) -> NotificationContentDTO:
    return resolve_plan_notification_content(user_id=user_id, plan_id=plan_id)
