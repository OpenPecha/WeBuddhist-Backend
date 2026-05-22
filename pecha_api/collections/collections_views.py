from __future__ import annotations

from fastapi import APIRouter, Query, Response
from starlette import status
from typing import Optional

from ..collections.collections_service import get_all_collections

collections_router = APIRouter(
    prefix="/collections",
    tags=["collections"]
)

DEPRECATION_DATE = "Sat, 01 Jun 2026 00:00:00 GMT"
V2_ENDPOINT = "/api/v2/collections"


@collections_router.get(
    "",
    status_code=status.HTTP_200_OK,
    deprecated=True,
    summary="Get collections (DEPRECATED)",
    description="**DEPRECATED**: This endpoint will be removed on June 1, 2026. Please migrate to /api/v2/collections."
)
async def read_collection(
        response: Response,
        parent_id: Optional[str] = Query(None, description="Filter topics by title prefix"),
        language: Optional[str] = None,
        skip: int = Query(default=0, ge=0, description="Number of records to skip"),
        limit: int = Query(default=10, ge=1, le=100, description="Number of records to return")
):
    response.headers["Deprecation"] = "true"
    response.headers["Sunset"] = DEPRECATION_DATE
    response.headers["Link"] = f"<{V2_ENDPOINT}>; rel=\"successor-version\""
    return await get_all_collections(
        parent_id=parent_id,
        language=language,
        skip=skip,
        limit=limit
    )
