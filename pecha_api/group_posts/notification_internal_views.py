from uuid import UUID

from fastapi import APIRouter, Depends, Query
from starlette import status

from pecha_api.group_posts.notification_response_models import GroupPostNotificationTargetsResponse
from pecha_api.group_posts.notification_service import get_group_post_notification_targets
from pecha_api.routines.routine_notifications.dependencies import verify_dispatch_token

internal_group_post_notifications_router = APIRouter(
    prefix="/internal",
    tags=["Internal"],
)


@internal_group_post_notifications_router.get(
    "/group-post-notification-targets/{post_id}",
    status_code=status.HTTP_200_OK,
)
def group_post_notification_targets(
    post_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    _: None = Depends(verify_dispatch_token),
) -> GroupPostNotificationTargetsResponse:
    return get_group_post_notification_targets(post_id=post_id, skip=skip, limit=limit)
