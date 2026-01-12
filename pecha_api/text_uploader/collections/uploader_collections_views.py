from fastapi import APIRouter
from starlette import status
from typing import Optional

from pecha_api.collections.collections_service import get_collection_by_pecha_collection_id_service
text_uploader_collections_router = APIRouter(
    prefix="/text-uploader/collections",
    tags=["Text Uploader"]
)

@text_uploader_collections_router.get("/{pecha_collection_id}", status_code=status.HTTP_200_OK)
async def get_collection_by_pecha_collection_id(pecha_collection_id: str) -> Optional[str]:
    return await get_collection_by_pecha_collection_id_service(
        pecha_collection_id=pecha_collection_id
    )