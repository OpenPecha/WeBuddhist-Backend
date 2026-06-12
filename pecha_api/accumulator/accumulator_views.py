from fastapi import APIRouter, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Annotated, Optional
from uuid import UUID
from starlette import status

from .accumulator_service import (
    get_all_accumulators_service,
    get_user_accumulators_service,
    create_accumulator_service,
    update_accumulator_service,
    delete_accumulator_service,
    record_accumulator_count_service,
    get_accumulator_history_service
)
from .accumulator_response_models import (
    AccumulatorsResponse,
    AccumulatorDTO,
    CreateAccumulatorRequest,
    UpdateAccumulatorRequest,
    RecordAccumulatorCountRequest,
    AccumulatorHistoryResponse
)
from ..users.users_service import validate_and_extract_user_details

accumulator_router = APIRouter(prefix="/accumulators", tags=["Accumulators"])
oauth2_scheme = HTTPBearer()


@accumulator_router.get("", response_model=AccumulatorsResponse)
async def get_all_accumulators(
    group_id: Optional[UUID] = Query(None, description="Group ID to filter accumulators"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records to return"),
):
    return get_all_accumulators_service(group_id=group_id, skip=skip, limit=limit)


@accumulator_router.get("/user", response_model=AccumulatorsResponse)
async def get_user_accumulators(
    group_id: Optional[UUID] = Query(None, description="Group ID to filter accumulators"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records to return"),
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)] = None
):
    current_user = validate_and_extract_user_details(token=credentials.credentials)
    return get_user_accumulators_service(
        user_id=current_user.id,
        group_id=group_id,
        skip=skip,
        limit=limit
    )


@accumulator_router.post("/user", status_code=status.HTTP_201_CREATED, response_model=AccumulatorDTO)
async def create_user_accumulator(
    request: CreateAccumulatorRequest,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)]
):
    return await create_accumulator_service(
        token=credentials.credentials,
        request=request
    )


@accumulator_router.put("/user/{accumulator_id}", response_model=AccumulatorDTO)
async def update_user_accumulator(
    accumulator_id: UUID,
    request: UpdateAccumulatorRequest,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)]
):
    return await update_accumulator_service(
        token=credentials.credentials,
        accumulator_id=accumulator_id,
        request=request
    )


@accumulator_router.delete("/user/{accumulator_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_accumulator(
    accumulator_id: UUID,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)]
):
    delete_accumulator_service(
        token=credentials.credentials,
        accumulator_id=accumulator_id
    )


@accumulator_router.post("/user/count", status_code=status.HTTP_201_CREATED, response_model=AccumulatorDTO)
async def record_accumulator_count(
    request: RecordAccumulatorCountRequest,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)]
):
    return record_accumulator_count_service(
        token=credentials.credentials,
        request=request
    )


@accumulator_router.get("/user/history", response_model=AccumulatorHistoryResponse)
async def get_user_accumulator_history(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records to return")
):
    return get_accumulator_history_service(
        token=credentials.credentials,
        skip=skip,
        limit=limit
    )
