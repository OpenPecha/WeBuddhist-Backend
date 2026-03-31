from fastapi import APIRouter, Depends, Path
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette import status
from typing import Annotated
from .routines_response_models import (
    CreateTimeBlockRequest,
    UpdateTimeBlockRequest,
    RoutineWithTimeBlocksResponse,
    TimeBlockDTO,
)
from .routines_service import create_routine_with_time_block, update_time_block_service

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


@routines_router.put("/{routine_id}/time-blocks/{time_block_id}", status_code=status.HTTP_201_CREATED, response_model=TimeBlockDTO)
async def update_time_block(
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
    routine_id: str = Path(...),
    time_block_id: str = Path(...),
    request: UpdateTimeBlockRequest = ...,
):
    return await update_time_block_service(
        token=authentication_credential.credentials,
        routine_id=routine_id,
        time_block_id=time_block_id,
        request=request,
    )
