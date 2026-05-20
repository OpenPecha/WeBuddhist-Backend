from __future__ import annotations

from fastapi import APIRouter
from starlette import status
from fastapi import Query

from .texts_openpecha_services import get_text_detail_by_id
from .text_openpecha_response_models import TextDetailResponse, TextDetailRequest

texts_v2_router = APIRouter(
    prefix="/v2/texts",
    tags=["texts-v2"]
)


@texts_v2_router.get(
    "/detail",
    response_model=TextDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a text with pagination",
    description="Retrieve a text by its OpenPecha ID, including local edition details with pagination."
)
async def read_text_by_id(text_id: str, offset: int = Query(default=0), limit: int = Query(default=30)) -> TextDetailResponse:
    return await get_text_detail_by_id(text_id=text_id, offset=offset, limit=limit)