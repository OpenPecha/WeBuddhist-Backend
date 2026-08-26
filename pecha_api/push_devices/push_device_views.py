from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette import status

from pecha_api.push_devices.push_device_enums import PushPlatform
from pecha_api.push_devices.push_device_response_models import (
    AdminPushDeviceTokensListResponse,
    PushDeviceTokenDTO,
    PushDeviceTokensResponse,
    RegisterPushDeviceRequest,
)
from pecha_api.push_devices.push_device_service import (
    delete_push_device_service,
    get_push_devices_service,
    list_all_push_devices_service,
    register_push_device_service,
)

oauth2_scheme = HTTPBearer()
push_device_router = APIRouter(
    prefix="/users/me",
    tags=["Push Devices"],
)

cms_push_device_router = APIRouter(
    prefix="/cms/push-devices",
    tags=["CMS Push Devices"],
)


@push_device_router.post(
    "/push-devices",
    status_code=status.HTTP_201_CREATED,
    response_model=PushDeviceTokenDTO,
)
async def register_push_device(
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
    register_request: RegisterPushDeviceRequest,
) -> PushDeviceTokenDTO:
    return await register_push_device_service(
        token=authentication_credential.credentials,
        register_request=register_request,
    )


@push_device_router.get(
    "/push-devices",
    status_code=status.HTTP_200_OK,
    response_model=PushDeviceTokensResponse,
)
async def get_push_devices(
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
) -> PushDeviceTokensResponse:
    return await get_push_devices_service(token=authentication_credential.credentials)


@push_device_router.delete(
    "/push-devices/{push_device_token_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_push_device(
    push_device_token_id: UUID,
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
) -> None:
    await delete_push_device_service(
        token=authentication_credential.credentials,
        push_device_token_id=push_device_token_id,
    )


@cms_push_device_router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=AdminPushDeviceTokensListResponse,
)
async def list_all_push_devices(
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    platform: Annotated[Optional[PushPlatform], Query()] = None,
    active_only: Annotated[bool, Query()] = True,
) -> AdminPushDeviceTokensListResponse:
    return await list_all_push_devices_service(
        token=authentication_credential.credentials,
        skip=skip,
        limit=limit,
        platform=platform,
        active_only=active_only,
    )
