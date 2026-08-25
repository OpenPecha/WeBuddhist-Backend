from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Query
from starlette import status

from pecha_api.poems.response_models import PoemDTO, PoemsResponse
from pecha_api.poems.service import get_poem_detail_service, list_poems_service

poems_router = APIRouter(
    prefix="/poems",
    tags=["Poems"],
)


@poems_router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=PoemsResponse,
)
def list_poems(
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    chapter_name: Annotated[
        Optional[str],
        Query(description="Filter by chapter name (exact match)"),
    ] = None,
    author_name: Annotated[
        Optional[str],
        Query(description="Filter by author name (exact match)"),
    ] = None,
) -> PoemsResponse:
    """List published poems, newest first."""
    return list_poems_service(
        skip=skip,
        limit=limit,
        chapter_name=chapter_name,
        author_name=author_name,
    )


@poems_router.get(
    "/{poem_id}",
    status_code=status.HTTP_200_OK,
    response_model=PoemDTO,
)
def get_poem_detail(poem_id: UUID) -> PoemDTO:
    """Get a published poem by ID with presigned image URL."""
    return get_poem_detail_service(poem_id=poem_id)
