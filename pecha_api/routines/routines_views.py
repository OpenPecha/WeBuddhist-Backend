from fastapi import APIRouter, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette import status
from typing import Annotated
from .routines_response_models import (
    CreateTimeBlockRequest,
    RoutineWithTimeBlocksResponse,
)
from .routines_service import create_routine_with_time_block

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
