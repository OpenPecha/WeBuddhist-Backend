from fastapi import APIRouter, Depends
from starlette import status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Annotated
from uuid import UUID

from pecha_api.bookmarks.bookmark_response_models import (
    CreateBookmarkRequest,
    BookmarksResponse,
    BookmarkDTO
)
from pecha_api.bookmarks.bookmark_services import (
    create_bookmark_service,
    get_bookmarks_service,
    delete_bookmark_service
)

oauth2_scheme = HTTPBearer()
bookmark_router = APIRouter(
    prefix="/users/me",
    tags=["Bookmarks"]
)


@bookmark_router.post("/bookmarks", status_code=status.HTTP_201_CREATED, response_model=BookmarkDTO)
async def create_bookmark(
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
    create_bookmark_request: CreateBookmarkRequest
):
    return await create_bookmark_service(
        token=authentication_credential.credentials,
        create_bookmark_request=create_bookmark_request
    )


@bookmark_router.get("/bookmarks", status_code=status.HTTP_200_OK, response_model=BookmarksResponse)
async def get_bookmarks(
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)]
):
    return await get_bookmarks_service(token=authentication_credential.credentials)


@bookmark_router.delete("/bookmarks/{bookmark_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bookmark(
    bookmark_id: UUID,
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)]
):
    return await delete_bookmark_service(
        token=authentication_credential.credentials,
        bookmark_id=bookmark_id
    )
