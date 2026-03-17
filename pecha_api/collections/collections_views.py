from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette import status
from typing import Annotated, Optional

from ..collections.collections_response_models import CreateCollectionRequest, UpdateCollectionRequest
from ..collections.collections_service import (
    get_all_collections, 
    create_new_collection, 
    update_existing_collection, 
    delete_existing_collection, 
    get_collection_by_pecha_collection_id_service
)

oauth2_scheme = HTTPBearer()
collections_router = APIRouter(
    prefix="/collections",
    tags=["collections"]
)

DEPRECATION_DATE = "Sat, 01 Jun 2026 00:00:00 GMT"
V2_ENDPOINT = "/api/v2/collections"


@collections_router.get(
    "",
    status_code=status.HTTP_200_OK,
    deprecated=True,
    summary="Get collections (DEPRECATED)",
    description="**DEPRECATED**: This endpoint will be removed on June 1, 2026. Please migrate to /api/v2/collections."
)
async def read_collection(
        response: Response,
        parent_id: Optional[str] = Query(None, description="Filter topics by title prefix"),
        language: Optional[str] = None,
        skip: int = Query(default=0, ge=0, description="Number of records to skip"),
        limit: int = Query(default=10, ge=1, le=100, description="Number of records to return")
):
    response.headers["Deprecation"] = "true"
    response.headers["Sunset"] = DEPRECATION_DATE
    response.headers["Link"] = f"<{V2_ENDPOINT}>; rel=\"successor-version\""
    return await get_all_collections(
        parent_id=parent_id,
        language=language,
        skip=skip,
        limit=limit
    )


@collections_router.post(
    "", 
    status_code=status.HTTP_201_CREATED,
    deprecated=True,
    summary="Create collection (DEPRECATED)",
    description="**DEPRECATED**: This endpoint will be removed on June 1, 2026. Please migrate to /api/v2/collections."
)
async def create_collection(language: str | None, create_collection_request: CreateCollectionRequest,
                       authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)]):
    return await create_new_collection(
        create_collection_request=create_collection_request,
        token=authentication_credential.credentials,
        language=language
    )


@collections_router.put(
    "/{collection_id}", 
    status_code=status.HTTP_202_ACCEPTED,
    deprecated=True,
    summary="Update collection (DEPRECATED)",
    description="**DEPRECATED**: This endpoint will be removed on June 1, 2026. Please migrate to /api/v2/collections."
)
async def update_collection_by_id(collection_id: str, language: str | None, update_collection_request: UpdateCollectionRequest,
                            authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)]):
    return await update_existing_collection(
        collection_id=collection_id,
        update_collection_request=update_collection_request,
        token=authentication_credential.credentials,
        language=language
    )


@collections_router.delete(
    "/{collection_id}", 
    status_code=status.HTTP_204_NO_CONTENT,
    deprecated=True,
    summary="Delete collection (DEPRECATED)",
    description="**DEPRECATED**: This endpoint will be removed on June 1, 2026. Please migrate to /api/v2/collections."
)
async def delete_collection_by_id(collection_id: str,
                            authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)]):
    return await delete_existing_collection(
        collection_id=collection_id,
        token=authentication_credential.credentials
    )

