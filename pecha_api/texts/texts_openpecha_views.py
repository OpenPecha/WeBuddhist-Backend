<<<<<<< HEAD
from __future__ import annotations

from fastapi import APIRouter
from starlette import status
from fastapi import Query

from .texts_openpecha_services import get_text_detail_by_id
from .text_openpecha_response_models import TextDetailResponse, TextDetailRequest

texts_v2_router = APIRouter(
    prefix="/v2/texts",
    tags=["texts-v2"]
=======
from typing import Annotated

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
>>>>>>> 84761972ac523b2c0d18e6e45f16c08fa0ecc7bc
)


@texts_v2_router.get(
<<<<<<< HEAD
    "/detail",
    response_model=TextDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a text with pagination",
    description="Retrieve a text by its OpenPecha ID, including local edition details with pagination."
)
async def read_text_by_id(text_id: str, offset: int = Query(default=0), limit: int = Query(default=30)) -> TextDetailResponse:
    return await get_text_detail_by_id(text_id=text_id, offset=offset, limit=limit)
=======
    "/collection/{collection_id}",
    status_code=status.HTTP_200_OK,
    summary="Get texts by collection from OpenPecha",
    description="Retrieve texts for a collection from OpenPecha API. "
)
async def get_texts_by_collection(
    collection_id: str,
    skip: Annotated[int, Query(ge=0, description="Number of records to skip")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="Number of records to return")] = 10,
) -> V2TextsCategoryResponse:
    return await get_texts_by_collection_from_openpecha(
        collection_id=collection_id,
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
>>>>>>> 84761972ac523b2c0d18e6e45f16c08fa0ecc7bc
