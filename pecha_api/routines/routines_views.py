from fastapi import APIRouter, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette import status
from typing import Annotated
from .routines_response_models import (
    CreateTimeBlockRequest,
    RoutineWithTimeBlocksResponse,
    RoutineResponse,
)
from .routines_service import create_routine_with_time_block, get_user_routine

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
):
    return await create_routine_with_time_block(
        token=authentication_credential.credentials,
        request=request,
    )


@user_routine_router.get("/routine", status_code=status.HTTP_200_OK, response_model=RoutineResponse)
async def get_routine(
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    return await get_user_routine(
        token=authentication_credential.credentials,
        skip=skip,
        limit=limit,
    )
