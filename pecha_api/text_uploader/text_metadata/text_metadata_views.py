from fastapi import APIRouter
from starlette import status
from typing import Optional, List

from pecha_api.texts.texts_response_models import TextDTO
from pecha_api.texts.texts_response_models import TextsByPechaTextIdsRequest
from pecha_api.texts.texts_service import get_text_by_pecha_text_ids_service

text_metadata_router = APIRouter(
    prefix="/text-uploader",
    tags=["Text Uploader"]
)

@text_metadata_router.post("/list", status_code=status.HTTP_200_OK)
async def get_text_by_pecha_text_ids(texts_by_pecha_text_ids_request: TextsByPechaTextIdsRequest) -> Optional[List[TextDTO]]:
    return await get_text_by_pecha_text_ids_service(texts_by_pecha_text_ids_request=texts_by_pecha_text_ids_request)    