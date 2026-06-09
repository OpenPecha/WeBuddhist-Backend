from typing import Optional

from fastapi import APIRouter, Query
from starlette import status

from .search_enums import V2ContentSearchType
from .search_openpecha_service import get_v2_multilingual_search_results
from .search_response_models import MultilingualSearchResponse

search_v2_router = APIRouter(
    prefix="/v2/search",
    tags=["search-v2"],
)


@search_v2_router.get("/multilingual", status_code=status.HTTP_200_OK)
async def multilingual_search_v2(
    query: str = Query(...),
    search_type: V2ContentSearchType = Query(default=V2ContentSearchType.SIMILAR),
    text_id: Optional[str] = Query(default=None),
    edition_id: Optional[str] = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
) -> MultilingualSearchResponse:
    return await get_v2_multilingual_search_results(
        query=query,
        search_type=search_type.value,
        text_id=text_id,
        edition_id=edition_id,
        skip=skip,
        limit=limit,
    )
