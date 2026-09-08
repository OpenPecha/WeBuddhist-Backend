from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from starlette import status

from pecha_api.plans.groups.join_request_notification_response_models import (
    JoinRequestNotificationTargetsResponse,
)
from pecha_api.plans.groups.join_request_notification_service import (
    get_join_request_notification_targets,
)
from pecha_api.routines.routine_notifications.dependencies import verify_dispatch_token

internal_join_request_notifications_router = APIRouter(
    prefix="/internal",
    tags=["Internal"],
)


@internal_join_request_notifications_router.get(
    "/join-request-notification-targets/{join_request_id}",
    status_code=status.HTTP_200_OK,
)
def join_request_notification_targets(
    join_request_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    event_type: Optional[str] = Query(
        None,
        description=(
            "The queued event type (JOIN_REQUEST_CREATED or JOIN_REQUEST_DECIDED). "
            "Pass it so a late event notifies the right audience; omitted, the "
            "current request status decides."
        ),
    ),
    _: None = Depends(verify_dispatch_token),
) -> JoinRequestNotificationTargetsResponse:
    return get_join_request_notification_targets(
        join_request_id=join_request_id,
        skip=skip,
        limit=limit,
        event_type=event_type,
    )
