from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette import status

from pecha_api.users.users_service import validate_and_extract_user_details

from pecha_api.group_recitation_collection.response_models import (
    GroupRecitationCollectionDetailDTO,
    GroupRecitationCollectionsResponse,
)
from pecha_api.group_recitation_collection.service import (
    get_group_collection_detail_service,
    list_group_collections_service,
)

oauth2_scheme_optional = HTTPBearer(auto_error=False)

public_group_recitation_collection_router = APIRouter(
    prefix="/author/groups/{group_id}/recitation-collections",
    tags=["Public Group Recitation Collections"],
)

public_group_recitation_collection_detail_router = APIRouter(
    prefix="/author/groups/recitation-collections",
    tags=["Public Group Recitation Collections"],
)


@public_group_recitation_collection_router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=GroupRecitationCollectionsResponse,
)
async def list_group_recitation_collections(
    group_id: UUID,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    x_timezone: Annotated[
        Optional[str],
        Header(
            alias="X-Timezone",
            description="IANA timezone (e.g. Asia/Shanghai). Restricted collections are hidden for Chinese timezones.",
        ),
    ] = None,
    authentication_credential: Annotated[
        Optional[HTTPAuthorizationCredentials], Depends(oauth2_scheme_optional)
    ] = None,
):
    """List a group's recitation collections."""
    user_id = None
    if authentication_credential:
        try:
            user = validate_and_extract_user_details(
                token=authentication_credential.credentials
            )
            user_id = user.id
        except Exception:
            pass
    return await list_group_collections_service(
        group_id=group_id,
        skip=skip,
        limit=limit,
        timezone_name=x_timezone,
        user_id=user_id,
    )


@public_group_recitation_collection_router.get(
    "/{collection_id}",
    status_code=status.HTTP_200_OK,
    response_model=GroupRecitationCollectionDetailDTO,
)
async def get_group_recitation_collection_detail_by_group(
    group_id: UUID,
    collection_id: UUID,
    x_timezone: Annotated[
        Optional[str],
        Header(
            alias="X-Timezone",
            description="IANA timezone (e.g. Asia/Shanghai). Restricted collections are hidden for Chinese timezones.",
        ),
    ] = None,
    authentication_credential: Annotated[
        Optional[HTTPAuthorizationCredentials], Depends(oauth2_scheme_optional)
    ] = None,
):
    """Get a specific recitation collection with its items (group-scoped)."""
    user_id = None
    if authentication_credential:
        try:
            user = validate_and_extract_user_details(
                token=authentication_credential.credentials
            )
            user_id = user.id
        except Exception:
            pass
    return await get_group_collection_detail_service(
        collection_id=collection_id,
        timezone_name=x_timezone,
        group_id=group_id,
        user_id=user_id,
    )


@public_group_recitation_collection_detail_router.get(
    "/{collection_id}",
    status_code=status.HTTP_200_OK,
    response_model=GroupRecitationCollectionDetailDTO,
)
async def get_group_recitation_collection_detail(
    collection_id: UUID,
    x_timezone: Annotated[
        Optional[str],
        Header(
            alias="X-Timezone",
            description="IANA timezone (e.g. Asia/Shanghai). Restricted collections are hidden for Chinese timezones.",
        ),
    ] = None,
    authentication_credential: Annotated[
        Optional[HTTPAuthorizationCredentials], Depends(oauth2_scheme_optional)
    ] = None,
):
    """Get a specific recitation collection with its items."""
    user_id = None
    if authentication_credential:
        try:
            user = validate_and_extract_user_details(
                token=authentication_credential.credentials
            )
            user_id = user.id
        except Exception:
            pass
    return await get_group_collection_detail_service(
        collection_id=collection_id,
        timezone_name=x_timezone,
        user_id=user_id,
    )
