from __future__ import annotations

from fastapi import APIRouter, Query
from starlette import status
from typing import Optional

from .collections_response_models import CollectionsResponse
from .collections_openpecha_service import get_collections_from_openpecha

collections_v2_router = APIRouter(
    prefix="/v2/collections",
    tags=["collections-v2"]
)


@collections_v2_router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=CollectionsResponse,
    summary="Get collections from OpenPecha",
    description="Retrieve collections/categories from OpenPecha API with optional filtering by parent_id and language."
)
async def read_collections_v2(
    parent_id: Optional[str] = Query(None, description="Filter by parent category ID"),
    language: Optional[str] = Query(None, description="Language code (e.g., 'en', 'bo', 'zh')"),
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=10, ge=1, le=100, description="Number of records to return")
) -> CollectionsResponse:
    return await get_collections_from_openpecha(
        parent_id=parent_id,
        language=language,
        skip=skip,
        limit=limit
    )
