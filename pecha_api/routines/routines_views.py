from fastapi import APIRouter, Depends, Header, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from uuid import UUID
from starlette import status
from typing import Annotated, Optional
from pecha_api.plans.language_constants import language_query_description
from .routines_response_models import (
    CreateTimeBlockRequest,
    TimeBlockDTO,
    UpdateTimeBlockRequest,
    RoutineWithTimeBlocksResponse,
    RoutineResponse,
    RoutineInfoResponse,
)
from .routines_service import create_routine_with_time_block, add_time_block_to_routine, delete_time_block, update_time_block_service, get_user_routine, get_user_routine_info

oauth2_scheme = HTTPBearer()

routines_router = APIRouter(
    prefix="/routines",
    tags=["User Routines"],
)

user_routine_router = APIRouter(
    prefix="/users/me",
    tags=["User Routines"],
)


@routines_router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=RoutineWithTimeBlocksResponse,
)
async def create_routine(
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
    request: CreateTimeBlockRequest,
    x_timezone: Annotated[
        Optional[str],
        Header(alias="X-Timezone", description="IANA timezone of the user (e.g. 'Asia/Kathmandu'). Stored on the routine; null if not provided."),
    ] = None,
):
    return await create_routine_with_time_block(
        token=authentication_credential.credentials,
        request=request,
        timezone_name=x_timezone,
    )


@routines_router.post(
    "/{routine_id}/time-blocks",
    status_code=status.HTTP_201_CREATED,
    response_model=TimeBlockDTO,
)
async def create_time_block(
    routine_id: UUID,
    authentication_credential: Annotated[
        HTTPAuthorizationCredentials, Depends(oauth2_scheme)
    ],
    request: CreateTimeBlockRequest,
    x_timezone: Annotated[
        Optional[str],
        Header(alias="X-Timezone", description="IANA timezone of the user (e.g. 'Asia/Kathmandu'). When provided, refreshes the routine's stored timezone."),
    ] = None,
):
    return await add_time_block_to_routine(
        token=authentication_credential.credentials,
        routine_id=routine_id,
        request=request,
        timezone_name=x_timezone,
    )


@routines_router.delete(
    "/{routine_id}/time-blocks/{time_block_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_time_block_view(
    routine_id: UUID,
    time_block_id: UUID,
    authentication_credential: Annotated[
        HTTPAuthorizationCredentials, Depends(oauth2_scheme)
    ],
):
    delete_time_block(
        token=authentication_credential.credentials,
        routine_id=routine_id,
        time_block_id=time_block_id,
    )


@routines_router.put("/{routine_id}/time-blocks/{time_block_id}", status_code=status.HTTP_201_CREATED, response_model=TimeBlockDTO)
async def update_time_block(
    routine_id: UUID,
    time_block_id: UUID,
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
    request: UpdateTimeBlockRequest,
    x_timezone: Annotated[
        Optional[str],
        Header(alias="X-Timezone", description="IANA timezone of the user (e.g. 'Asia/Kathmandu'). When provided, refreshes the routine's stored timezone."),
    ] = None,
):
    return await update_time_block_service(
        token=authentication_credential.credentials,
        routine_id=routine_id,
        time_block_id=time_block_id,
        request=request,
        timezone_name=x_timezone,
    )


@user_routine_router.get("/routine", status_code=status.HTTP_200_OK, response_model=RoutineResponse)
async def get_routine(
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    language: Annotated[
        Optional[str],
        Query(description=language_query_description("Render session titles in this language, falling back to 'en'", lowercase_example=True)),
    ] = None,
):
    return await get_user_routine(
        token=authentication_credential.credentials,
        skip=skip,
        limit=limit,
        language=language,
    )


@user_routine_router.get(
    "/routine/info",
    status_code=status.HTTP_200_OK,
    response_model=RoutineInfoResponse,
)
async def get_routine_info(
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
):
    return await get_user_routine_info(
        token=authentication_credential.credentials,
    )
