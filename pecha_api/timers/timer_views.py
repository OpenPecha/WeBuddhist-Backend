from fastapi import APIRouter, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Annotated
from uuid import UUID

from .timer_service import get_all_timers_service, get_user_timers_service
from .timer_response_models import TimersResponse
from ..users.users_service import validate_and_extract_user_details

timer_router = APIRouter(prefix="/timers", tags=["Timers"])
oauth2_scheme = HTTPBearer()


@timer_router.get("", response_model=TimersResponse)
async def get_all_timers(
    group_id: UUID = Query(..., description="Group ID to filter timers"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records to return"),
):
    return get_all_timers_service(group_id=group_id, skip=skip, limit=limit)


@timer_router.get("/user", response_model=TimersResponse)
async def get_user_timers(
    group_id: UUID = Query(..., description="Group ID to filter timers"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records to return"),
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)] = None
):
    current_user = validate_and_extract_user_details(token=credentials.credentials)
    return get_user_timers_service(
        user_id=current_user.id,
        group_id=group_id,
        skip=skip,
        limit=limit
    )
