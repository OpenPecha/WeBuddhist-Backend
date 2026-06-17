from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette import status

from pecha_api.plans.notifications.day_notification_response_models import (
    CreateNotificationRequest,
    NotificationDTO,
    UpdateNotificationRequest,
)
from pecha_api.plans.notifications.day_notification_service import (
    create_day_notification,
    delete_day_notification,
    get_day_notification,
    update_day_notification,
)

oauth2_scheme = HTTPBearer()

notifications_router = APIRouter(
    prefix="/cms/notifications",
    tags=["Notifications"],
)


@notifications_router.post(
    "/{day_id}",
    status_code=status.HTTP_201_CREATED,
    response_model=NotificationDTO,
)
async def create_notification(
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
    day_id: UUID,
    request: CreateNotificationRequest,
):
    return create_day_notification(
        token=authentication_credential.credentials,
        day_id=day_id,
        request=request,
    )


@notifications_router.get(
    "/{day_id}",
    status_code=status.HTTP_200_OK,
    response_model=NotificationDTO,
)
async def get_notification(
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
    day_id: UUID,
):
    return get_day_notification(
        token=authentication_credential.credentials,
        day_id=day_id,
    )


@notifications_router.put(
    "/{day_id}",
    status_code=status.HTTP_200_OK,
    response_model=NotificationDTO,
)
async def update_notification(
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
    day_id: UUID,
    request: UpdateNotificationRequest,
):
    return update_day_notification(
        token=authentication_credential.credentials,
        day_id=day_id,
        request=request,
    )


@notifications_router.delete(
    "/{day_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_notification(
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
    day_id: UUID,
):
    return delete_day_notification(
        token=authentication_credential.credentials,
        day_id=day_id,
    )
