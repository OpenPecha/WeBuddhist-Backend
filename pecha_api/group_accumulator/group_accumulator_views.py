from fastapi import APIRouter, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Annotated
from uuid import UUID
from starlette import status

from .group_accumulator_service import (
    get_group_accumulator_service,
    submit_group_count_service,
    get_group_accumulator_history_service,
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
    "/{group_accumulator_id}/count",
    status_code=status.HTTP_201_CREATED,
    response_model=GroupAccumulatorHistoryItemDTO
)
async def submit_group_count(
    group_accumulator_id: UUID,
    request: SubmitGroupCountRequest,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
):
    """Submit user's count contribution to a group accumulator."""
    return submit_group_count_service(
        token=credentials.credentials,
        group_accumulator_id=group_accumulator_id,
        request=request,
    )


@group_accumulator_router.get(
    "/{group_accumulator_id}/count",
    response_model=GroupAccumulatorHistoryResponse
)
async def get_group_accumulator_history(
    group_accumulator_id: UUID,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records to return"),
):
    """Get history of all user contributions to a group accumulator."""
    return get_group_accumulator_history_service(
        group_accumulator_id=group_accumulator_id,
        skip=skip,
        limit=limit,
    )
