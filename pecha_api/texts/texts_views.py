from fastapi import APIRouter, Query, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette import status

from typing import Optional, Annotated, List

from .texts_service import (
    get_table_of_contents_by_text_id,
    get_text_versions_by_group_id,
    create_new_text,
    get_text_by_text_id_or_collection,
    get_text_details_by_text_id,
    create_table_of_content,
    get_text_details_by_text_id,
    get_commentaries_by_text_id,
    get_titles_and_ids_by_query
)
from .texts_response_models import (
    CreateTextRequest,
    TableOfContentResponse,
    TextDetailsRequest,
    TableOfContent,
    TextDTO,
    TextVersionResponse,
    DetailTableOfContentResponse,
    TextDetailsRequest
)

oauth2_scheme = HTTPBearer()
text_router = APIRouter(
    prefix="/texts",
    tags=["Texts"]
)


@text_router.get("", status_code=status.HTTP_200_OK)
async def get_text(
    text_id: Optional[str] = Query(default=None),
    collection_id: Optional[str] = Query(default=None),
    language: str = Query(default=None),
    skip: int = Query(default=0),
    limit: int = Query(default=10)
):
    return await get_text_by_text_id_or_collection(
        text_id=text_id,
        collection_id=collection_id,
        language=language,
        skip=skip,
        limit=limit
    )


@text_router.post("", status_code=status.HTTP_201_CREATED)
async def create_text(
    create_text_request: CreateTextRequest,
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
) -> TextDTO:
    return await create_new_text(
        create_text_request=create_text_request,
        token=authentication_credential.credentials
    )


@text_router.get("/{text_id}/versions", status_code=status.HTTP_200_OK)
async def get_versions(
        text_id: str,
        language: str = Query(default=None),
        skip: int = Query(default=0),
        limit: int = Query(default=10)
) -> TextVersionResponse:
    return await get_text_versions_by_group_id(
        text_id=text_id,
        language=language, skip=skip, limit=limit
    )


@text_router.get("/{text_id}/contents", status_code=status.HTTP_200_OK)
async def get_contents(
        text_id: str,
        language: str = Query(default=None),
        skip: int = Query(default=0),
        limit: int = Query(default=10)
) -> TableOfContentResponse:
    return await get_table_of_contents_by_text_id(text_id=text_id, language=language, skip=skip, limit=limit)


@text_router.post("/{text_id}/details", status_code=status.HTTP_200_OK)
async def get_contents_with_details(
        text_id: str,
        text_details_request: TextDetailsRequest
) -> DetailTableOfContentResponse:
    return await get_text_details_by_text_id(text_id=text_id, text_details_request=text_details_request)

@text_router.post("/table-of-content", status_code=status.HTTP_200_OK)
async def create_table_of_content_request(
        authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
        table_of_content_request: TableOfContent
):
    return await create_table_of_content(table_of_content_request=table_of_content_request, token=authentication_credential.credentials)

@text_router.get("/{text_id}/commentaries", status_code=status.HTTP_200_OK)
async def get_commentaries(
        text_id: str,
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=10, le=100)
) -> List[TextDTO]:
    return await get_commentaries_by_text_id(text_id=text_id, skip=skip, limit=limit)

@text_router.get("/title-search", status_code=status.HTTP_200_OK)
async def search_titles(
    title: Optional[str] = Query(default=None, description="Filter by title"),
    author: Optional[str] = Query(default=None, description="Filter by author"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
) -> List[dict]:
    return await get_titles_and_ids_by_query(
        title=title,
        author=author,
        limit=limit,
        offset=offset
    )