from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette import status

from pecha_api.notification.notification_response_models import (
    NotificationDTO,
    NotificationListResponse,
)
from pecha_api.notification.notification_service import (
    list_notifications,
    mark_notification_as_read,
)

oauth2_scheme = HTTPBearer()

cms_notifications_router = APIRouter(
    prefix="/cms/notifications",
    tags=["CMS Notifications"],
)


@cms_notifications_router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=NotificationListResponse,
)
def get_notifications(
    authentication_credential: Annotated[
        HTTPAuthorizationCredentials, Depends(oauth2_scheme)
    ],
    unread_only: Annotated[bool, Query()] = False,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    return list_notifications(
        token=authentication_credential.credentials,
        skip=skip,
        limit=limit,
        unread_only=unread_only,
    )


@cms_notifications_router.patch(
    "/{notification_id}/read",
    status_code=status.HTTP_200_OK,
    response_model=NotificationDTO,
)
def patch_mark_notification_read(
    notification_id: UUID,
    authentication_credential: Annotated[
        HTTPAuthorizationCredentials, Depends(oauth2_scheme)
    ],
):
    return mark_notification_as_read(
        token=authentication_credential.credentials,
        notification_id=notification_id,
    )
