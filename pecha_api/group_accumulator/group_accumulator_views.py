from fastapi import APIRouter, Depends, Query, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Annotated
from uuid import UUID
from starlette import status

from .group_accumulator_service import (
    get_group_accumulator_service,
    submit_group_count_service,
    get_group_accumulator_history_service,
    delete_group_accumulator_user_service,
)
from .group_accumulator_response_models import (
    SubmitGroupCountRequest,
    GroupAccumulatorDetailDTO,
    GroupAccumulatorHistoryResponse,
    GroupAccumulatorHistoryItemDTO,
)

group_accumulator_router = APIRouter(prefix="/group-accumulators", tags=["Group Accumulators"])
oauth2_scheme = HTTPBearer()


@group_accumulator_router.get("/{group_accumulator_id}", response_model=GroupAccumulatorDetailDTO)
async def get_group_accumulator(
    group_accumulator_id: UUID,
):
    """Get group accumulator details including total count from all users."""
    return get_group_accumulator_service(group_accumulator_id=group_accumulator_id)


@group_accumulator_router.post(
    "/{group_accumulator_id}",
    response_model=GroupAccumulatorHistoryItemDTO,
    responses={
        201: {"description": "New history entry created"},
        200: {"description": "No change (delta <= 0)"},
    }
)
async def submit_group_count(
    group_accumulator_id: UUID,
    request: SubmitGroupCountRequest,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
    response: Response,
):
    result, is_created = submit_group_count_service(
        token=credentials.credentials,
        group_accumulator_id=group_accumulator_id,
        request=request,
    )
    response.status_code = status.HTTP_201_CREATED if is_created else status.HTTP_200_OK
    return result


@group_accumulator_router.put(
    "/{group_accumulator_id}",
    response_model=GroupAccumulatorHistoryItemDTO,
    responses={
        201: {"description": "New history entry created"},
        200: {"description": "No change (delta <= 0)"},
    }
)
async def update_group_count(
    group_accumulator_id: UUID,
    request: SubmitGroupCountRequest,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
    response: Response,
):
    result, is_created = submit_group_count_service(
        token=credentials.credentials,
        group_accumulator_id=group_accumulator_id,
        request=request,
    )
    response.status_code = status.HTTP_201_CREATED if is_created else status.HTTP_200_OK
    return result


@group_accumulator_router.get(
    "/{group_accumulator_id}/history",
    response_model=GroupAccumulatorHistoryResponse
)
async def get_group_accumulator_history(
    group_accumulator_id: UUID,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records to return"),
):
    return get_group_accumulator_history_service(
        group_accumulator_id=group_accumulator_id,
        skip=skip,
        limit=limit,
    )


@group_accumulator_router.delete(
    "/{group_accumulator_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_group_accumulator(
    group_accumulator_id: UUID,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
):
    """Soft delete (reset) a group accumulator. Requires user to be a member of the group."""
    delete_group_accumulator_user_service(
        token=credentials.credentials,
        group_accumulator_id=group_accumulator_id,
    )
    return None
