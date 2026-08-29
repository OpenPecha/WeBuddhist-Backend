from typing import Annotated, Optional, List

from fastapi import APIRouter, HTTPException, Query
from starlette import status

from .texts_response_models import (
    TextDTO,
    TextVersionResponse,
    TitleSearchResult,
    V2TextDTO,
    V2TextsCategoryResponse,
)
from .texts_openpecha_service import (
    get_texts_by_collection_from_openpecha,
    get_text_by_id_from_openpecha,
    get_text_details_by_text_id_from_openpecha,
    get_text_versions_from_openpecha,
    get_text_commentaries_from_openpecha,
    get_titles_by_query_from_openpecha,
)
from pecha_api.texts.text_openpecha_response_models import (
    TextDetailsRequest,
    TextDetailWithContentResponse,
)

texts_v2_router = APIRouter(
    prefix="/texts",
    tags=["texts-v2"],
)

@texts_v2_router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="Get texts by collection from OpenPecha",
    description="Retrieve texts for a collection from OpenPecha API. "
)
async def get_texts_by_collection(
    collection_id: Annotated[Optional[str], Query(description="Collection ID to filter texts")] = None,
    language: Annotated[Optional[str], Query(description="Language code filter")] = None,
    title: Annotated[Optional[str], Query(description="Filter texts by title (case-insensitive substring)")] = None,
    skip: Annotated[int, Query(ge=0, description="Number of records to skip")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="Number of records to return")] = 10,
) -> V2TextsCategoryResponse:
    return await get_texts_by_collection_from_openpecha(
        collection_id=collection_id,
        language=language,
        title=title,
        skip=skip,
        limit=limit,
    )

@texts_v2_router.get(
    "/title-search",
    status_code=status.HTTP_200_OK,
    summary="Search texts by title from OpenPecha",
    description="Search texts by title via the OpenPecha API. Returns OpenPecha text ids.",
)
async def search_titles(
    title: Annotated[str, Query(description="Title to search for (case-insensitive substring)")],
    author: Annotated[Optional[str], Query(description="Not supported by OpenPecha; rejected if provided")] = None,
    limit: Annotated[int, Query(ge=1, le=100, description="Number of records to return")] = 20,
    offset: Annotated[int, Query(ge=0, description="Number of records to skip")] = 0,
) -> List[TitleSearchResult]:
    if author:
        # Rejected rather than ignored: silently dropping the filter would return
        # unfiltered results that look filtered.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="author filter is not supported by the OpenPecha title search",
        )
    return await get_titles_by_query_from_openpecha(
        title=title,
        limit=limit,
        offset=offset,
    )


@texts_v2_router.post(
    "/{text_id}/details",
    response_model=TextDetailWithContentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a text with its content and pagination",
    description=(
        "Retrieve a text by its OpenPecha ID with a page of segments. "
        "Paginate with segment_id + direction, or with an explicit start/end position range."
    ),
)
async def read_text_by_id(
    text_id: str,
    text_details_request: TextDetailsRequest,
) -> TextDetailWithContentResponse:
    return await get_text_details_by_text_id_from_openpecha(
        text_id=text_id,
        text_details_request=text_details_request,
    )


@texts_v2_router.get(
    "/{text_id}",
    status_code=status.HTTP_200_OK,
    summary="Get a single text by ID from OpenPecha",
    description="Retrieve a single text by its ID from the OpenPecha API.",
)
async def get_text_by_id(text_id: str) -> V2TextDTO:
    return await get_text_by_id_from_openpecha(text_id=text_id)


@texts_v2_router.get("/{text_id}/versions", status_code=status.HTTP_200_OK)
async def get_text_versions(
    text_id: str,
    skip: Annotated[int, Query(ge=0, description="Number of records to skip")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="Number of records to return")] = 10
) -> TextVersionResponse:
    return await get_text_versions_from_openpecha(
        text_id=text_id,
        skip=skip,
        limit=limit
    )


@texts_v2_router.get("/{text_id}/commentaries", status_code=status.HTTP_200_OK)
async def get_text_commentaries(
    text_id: str,
    skip: Annotated[int, Query(ge=0, description="Number of records to skip")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="Number of records to return")] = 10
) -> List[TextDTO]:
    return await get_text_commentaries_from_openpecha(
        text_id=text_id,
        skip=skip,
        limit=limit
    )


