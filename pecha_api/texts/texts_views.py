from typing import Optional, List

from fastapi import APIRouter, Query
from starlette import status

from .texts_service import get_titles_and_ids_by_query
from .texts_response_models import TitleSearchResult

text_router = APIRouter(
    prefix="/texts",
    tags=["Texts"],
)


@text_router.get("/title-search", status_code=status.HTTP_200_OK)
async def search_titles(
    title: Optional[str] = Query(default=None),
    author: Optional[str] = Query(default=None),
    limit: int = Query(default=20),
    offset: int = Query(default=0),
) -> List[TitleSearchResult]:
    return await get_titles_and_ids_by_query(
        title=title,
        author=author,
        limit=limit,
        offset=offset,
    )
