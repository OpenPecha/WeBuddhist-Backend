from fastapi import APIRouter, Query, Depends
from starlette import status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Annotated
from uuid import UUID

from pecha_api.plans.users.recitation_collection.recitation_collection_response_models import (
    RecitationCollectionsResponse,
    RecitationCollectionDetailDTO
)
from pecha_api.plans.users.recitation_collection.recitation_collection_service import (
    get_user_collections_service,
    get_collection_detail_service
)

oauth2_scheme = HTTPBearer()

recitation_collection_router = APIRouter(
    prefix="/users/me/recitation-collections",
    tags=["Recitation Collections"]
)


@recitation_collection_router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=RecitationCollectionsResponse
)
async def get_user_collections(
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=50)
):

    return await get_user_collections_service(
        token=authentication_credential.credentials,
        skip=skip,
        limit=limit
    )


@recitation_collection_router.get(
    "/{collection_id}",
    status_code=status.HTTP_200_OK,
    response_model=RecitationCollectionDetailDTO
)
async def get_collection_detail(
    collection_id: UUID,
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)]
):

    return await get_collection_detail_service(
        token=authentication_credential.credentials,
        collection_id=collection_id
    )
