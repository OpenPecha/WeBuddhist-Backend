from fastapi import APIRouter, Query, Depends
from starlette import status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Annotated
from uuid import UUID

from pecha_api.plans.users.recitation_collection.recitation_collection_response_models import (
    RecitationCollectionsResponse,
    RecitationCollectionDetailDTO,
    CreateCollectionRequest,
    CreateCollectionResponse,
    AddItemsRequest,
    AddItemsResponse
)
from pecha_api.plans.users.recitation_collection.recitation_collection_service import (
    get_user_collections_service,
    get_collection_detail_service,
    create_collection_service,
    add_items_to_collection_service,
    delete_collection_service
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


@recitation_collection_router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=CreateCollectionResponse
)
async def create_collection(
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
    request: CreateCollectionRequest
):

    return await create_collection_service(
        token=authentication_credential.credentials,
        request=request
    )


@recitation_collection_router.post(
    "/{collection_id}/items",
    status_code=status.HTTP_201_CREATED,
    response_model=AddItemsResponse
)
async def add_items_to_collection(
    collection_id: UUID,
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
    request: AddItemsRequest
):

    return await add_items_to_collection_service(
        token=authentication_credential.credentials,
        collection_id=collection_id,
        request=request
    )


@recitation_collection_router.delete(
    "/{collection_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
async def delete_collection(
    collection_id: UUID,
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)]
):

    await delete_collection_service(
        token=authentication_credential.credentials,
        collection_id=collection_id
    )
