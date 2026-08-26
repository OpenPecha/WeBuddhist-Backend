from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette import status

from pecha_api.poems.cms_service import (
    cms_create_poem_service,
    cms_delete_poem_service,
    cms_get_poem_detail_service,
    cms_list_poems_service,
    cms_update_poem_service,
)
from pecha_api.poems.enums import PoemStatus
from pecha_api.poems.response_models import (
    CreatePoemRequest,
    PoemDTO,
    PoemsResponse,
    UpdatePoemRequest,
)

oauth2_scheme = HTTPBearer()

cms_poems_router = APIRouter(
    prefix="/cms/poems",
    tags=["CMS Poems"],
)


@cms_poems_router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=PoemsResponse,
)
def cms_list_poems(
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    status_filter: Annotated[
        Optional[PoemStatus],
        Query(alias="status", description="Filter by status: DRAFT or PUBLISHED"),
    ] = None,
    chapter_name: Annotated[
        Optional[str],
        Query(description="Filter by chapter name (exact match)"),
    ] = None,
    author_name: Annotated[
        Optional[str],
        Query(description="Filter by author name (exact match)"),
    ] = None,
) -> PoemsResponse:
    """List poems for CMS (all statuses)."""
    return cms_list_poems_service(
        token=authentication_credential.credentials,
        skip=skip,
        limit=limit,
        status_filter=status_filter,
        chapter_name=chapter_name,
        author_name=author_name,
    )


@cms_poems_router.get(
    "/{poem_id}",
    status_code=status.HTTP_200_OK,
    response_model=PoemDTO,
)
def cms_get_poem_detail(
    poem_id: UUID,
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
) -> PoemDTO:
    """Get a specific poem (CMS)."""
    return cms_get_poem_detail_service(
        token=authentication_credential.credentials,
        poem_id=poem_id,
    )


@cms_poems_router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=PoemDTO,
)
def cms_create_poem(
    request: CreatePoemRequest,
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
) -> PoemDTO:
    """Create a new poem."""
    return cms_create_poem_service(
        token=authentication_credential.credentials,
        request=request,
    )


@cms_poems_router.patch(
    "/{poem_id}",
    status_code=status.HTTP_200_OK,
    response_model=PoemDTO,
)
def cms_update_poem(
    poem_id: UUID,
    request: UpdatePoemRequest,
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
) -> PoemDTO:
    """Update a poem (partial update)."""
    return cms_update_poem_service(
        token=authentication_credential.credentials,
        poem_id=poem_id,
        request=request,
    )


@cms_poems_router.delete(
    "/{poem_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def cms_delete_poem(
    poem_id: UUID,
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
) -> Response:
    """Soft delete a poem."""
    cms_delete_poem_service(
        token=authentication_credential.credentials,
        poem_id=poem_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
