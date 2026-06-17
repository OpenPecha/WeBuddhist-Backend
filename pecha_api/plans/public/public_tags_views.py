from typing import Annotated, Optional

from fastapi import APIRouter, Query
from starlette import status

from pecha_api.plans.public.plan_service import get_public_tags
from pecha_api.plans.tags.tag_response_models import PublicTagsListResponse

public_tags_router = APIRouter(prefix="/public/tags", tags=["Public Tags"])


@public_tags_router.get("", status_code=status.HTTP_200_OK, response_model=PublicTagsListResponse)
def get_tags(
    featured: Annotated[
        Optional[bool],
        Query(description="Filter by featured flag. Omit for all tags."),
    ] = None,
    search: Annotated[
        Optional[str],
        Query(description="Search by tag name."),
    ] = None,
    language: Annotated[
        Optional[str],
        Query(description="Language code (EN, BO, ZH, HI, NE, MN). Defaults to EN."),
    ] = "EN",
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    return get_public_tags(
        featured=featured,
        search=search,
        language=language,
        skip=skip,
        limit=limit,
    )
