from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import APIRouter, Depends, Query
from typing import Annotated
from starlette import status

from .groups_response_models import (
    CreateGroupRequest,
    GroupDTO
)
from .groups_service import (
    create_new_group,
    get_group_details
)

oauth2_scheme = HTTPBearer()
group_router = APIRouter(
    prefix="/groups",
    tags=["Groups"]
)

@group_router.get("/{group_id}", status_code=status.HTTP_200_OK)
async def get_group_by_id(
    group_id: str
) -> GroupDTO:
    return await get_group_details(
        group_id=group_id
    )

@group_router.post("", status_code=status.HTTP_201_CREATED)
async def create_group(
    create_group_request: CreateGroupRequest,
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
) -> GroupDTO:
    return await create_new_group(
        create_group_request=create_group_request,
        token=authentication_credential.credentials
    )
