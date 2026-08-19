from fastapi import APIRouter, Depends, Query
from fastapi.exceptions import RequestValidationError
from starlette import status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Annotated, Optional
from uuid import UUID
from pydantic import ValidationError
from pecha_api.bookmarks.bookmark_enums import BookmarkFilterType, BookmarkType
from pecha_api.plans.language_constants import language_query_description
from pecha_api.bookmarks.bookmark_response_models import (
    CreateBookmarkRequest,
    BookmarksResponse,
    BookmarkDTO,
    BookmarkExistsResponse,
    BookmarkExistsQuery,
)
from pecha_api.bookmarks.bookmark_services import (
    create_bookmark_service,
    get_bookmarks_service,
    delete_bookmark_service,
    bookmark_exists_service,
)

oauth2_scheme = HTTPBearer()
bookmark_router = APIRouter(
    prefix="/users/me",
    tags=["Bookmarks"]
)


def get_bookmark_exists_query(
    source_id: Annotated[str, Query(min_length=1)],
    type: Optional[BookmarkType] = None,
) -> BookmarkExistsQuery:
    try:
        return BookmarkExistsQuery(type=type, source_id=source_id)
    except ValidationError as exc:
        raise RequestValidationError(exc.errors()) from exc


@bookmark_router.post(
    "/bookmarks",
    status_code=status.HTTP_201_CREATED,
    response_model=BookmarkDTO,
    response_model_exclude_none=True,
)
async def create_bookmark(
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
    create_bookmark_request: CreateBookmarkRequest
):
    return await create_bookmark_service(
        token=authentication_credential.credentials,
        create_bookmark_request=create_bookmark_request
    )


@bookmark_router.get(
    "/bookmarks",
    status_code=status.HTTP_200_OK,
    response_model=BookmarksResponse,
    response_model_exclude_none=True,
)
async def get_bookmarks(
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
    type: Optional[BookmarkFilterType] = None,
    language: Annotated[
        Optional[str],
        Query(
            description=language_query_description(
                "Localize enriched bookmark data",
                lowercase_example=True,
            )
        ),
    ] = None,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records to return"),
):
    return await get_bookmarks_service(
        token=authentication_credential.credentials,
        type=type,
        language=language,
        skip=skip,
        limit=limit,
    )


@bookmark_router.get(
    "/bookmarks/exists",
    status_code=status.HTTP_200_OK,
    response_model=BookmarkExistsResponse,
    response_model_exclude_none=True,
)
async def bookmark_exists(
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
    bookmark_exists_query: Annotated[BookmarkExistsQuery, Depends(get_bookmark_exists_query)],
):
    return await bookmark_exists_service(
        token=authentication_credential.credentials,
        bookmark_exists_query=bookmark_exists_query,
    )


@bookmark_router.delete("/bookmarks/{bookmark_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bookmark(
    bookmark_id: UUID,
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)]
):
    return await delete_bookmark_service(
        token=authentication_credential.credentials,
        bookmark_id=bookmark_id
    )
