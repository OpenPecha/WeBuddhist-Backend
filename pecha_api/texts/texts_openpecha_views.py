from typing import Annotated, Optional, List

from fastapi import APIRouter, Query
from starlette import status

from .texts_response_models import (
    TextDTO,
    TextVersionResponse,
    V2TextDTO,
    V2TextsCategoryResponse,
)
from .texts_openpecha_service import (
    get_texts_by_collection_from_openpecha,
    get_text_by_id_from_openpecha,
    get_text_detail_by_id,
    get_text_versions_from_openpecha,
    get_text_commentaries_from_openpecha,
)
from pecha_api.texts.text_openpecha_response_models import TextDetailWithContentResponse, TextDetailsRequest

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

@texts_v2_router.post(
    "/{edition_id}/details",
    response_model=TextDetailWithContentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a text edition with bidirectional segment pagination",
    description="Retrieve a text edition by its OpenPecha edition ID, paging through its segments from an optional segment_id cursor in either direction."
)
async def read_text_by_id(
    edition_id: str,
    text_details_request: TextDetailsRequest
) -> TextDetailWithContentResponse:
    return await get_text_detail_by_id(edition_id=edition_id, text_details_request=text_details_request)


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


@texts_v2_router.get("/{text_id}/languages/{language}/versions", status_code=status.HTTP_200_OK)
async def get_text_versions_by_language(
    text_id: str,
    language: str,
    skip: Annotated[int, Query(ge=0, description="Number of records to skip")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="Number of records to return")] = 10
) -> TextVersionResponse:
    return await get_text_versions_from_openpecha(
        text_id=text_id,
        language=language,
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


