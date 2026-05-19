from typing import Annotated, Optional

from fastapi import APIRouter, Query
from starlette import status

from .texts_response_models import V2TextDTO, V2TextsCategoryResponse
from .texts_openpecha_service import (
    get_texts_by_collection_from_openpecha,
    get_text_by_id_from_openpecha,
)

texts_v2_router = APIRouter(
    prefix="/v2/texts",
    tags=["texts-v2"],
)


@texts_v2_router.get(
    "/collection/{collection_id}",
    status_code=status.HTTP_200_OK,
    summary="Get texts by collection from OpenPecha",
    description="Retrieve texts for a collection from OpenPecha API. "
)
async def get_texts_by_collection(
    collection_id: str,
    language: Annotated[Optional[str], Query(description="Language code (e.g., 'en', 'bo', 'zh')")] = None,
    skip: Annotated[int, Query(ge=0, description="Number of records to skip")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="Number of records to return")] = 10,
) -> V2TextsCategoryResponse:
    return await get_texts_by_collection_from_openpecha(
        collection_id=collection_id,
        language=language,
        skip=skip,
        limit=limit,
    )


@texts_v2_router.get(
    "/{text_id}",
    status_code=status.HTTP_200_OK,
    summary="Get a single text by ID from OpenPecha",
    description="Retrieve a single text by its ID from the OpenPecha API.",
)
async def get_text_by_id(text_id: str) -> V2TextDTO:
    return await get_text_by_id_from_openpecha(text_id=text_id)
