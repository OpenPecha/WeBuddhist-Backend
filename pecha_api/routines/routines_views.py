from fastapi import APIRouter, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from uuid import UUID
from starlette import status
from typing import Annotated
from .routines_response_models import (
    CreateTimeBlockRequest,
    TimeBlockDTO,
    UpdateTimeBlockRequest,
    RoutineWithTimeBlocksResponse,
)
from .routines_service import create_routine_with_time_block, add_time_block_to_routine, delete_time_block, update_time_block_service

oauth2_scheme = HTTPBearer()

routines_router = APIRouter(
    prefix="/routines",
    tags=["User Routines"],
)


@routines_router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=RoutineWithTimeBlocksResponse,
)
async def create_routine(
    authentication_credential: Annotated[
        HTTPAuthorizationCredentials, Depends(oauth2_scheme)
    ],
    request: CreateTimeBlockRequest,
):
    return await create_routine_with_time_block(
        token=authentication_credential.credentials,
        request=request,
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
):
    return await add_time_block_to_routine(
        token=authentication_credential.credentials,
        routine_id=routine_id,
        request=request,
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
):
    return await update_time_block_service(
        token=authentication_credential.credentials,
        routine_id=routine_id,
        time_block_id=time_block_id,
        request=request,
    )
