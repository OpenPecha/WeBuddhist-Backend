from __future__ import annotations

from fastapi import APIRouter
from starlette import status

from .texts_openpecha_services import TextDetailResponse, get_text_detail_by_id

texts_v2_router = APIRouter(
    prefix="/v2/texts",
    tags=["texts-v2"]
)


@texts_v2_router.get(
    "/{text_id}",
    response_model=TextDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a text",
    description="Retrieve a specific text by its ID from OpenPecha."
)
async def read_text_by_id(text_id: str) -> TextDetailResponse:
    return await get_text_detail_by_id(text_id=text_id)
