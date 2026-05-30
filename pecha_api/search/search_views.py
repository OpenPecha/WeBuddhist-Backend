from fastapi import APIRouter, Query, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .search_enums import MultilingualSearchType
from starlette import status

from typing import Optional, Annotated

from .search_service import (
    get_multilingual_search_results,
    get_url_link as get_url_link_service
)
from pecha_api.plans.cms.cms_plans_service import get_filtered_plans

from .search_response_models import (
    MultilingualSearchResponse,
    SegmentLinkResponse,
)
from pecha_api.plans.plans_response_models import PlansResponse

oauth2_scheme = HTTPBearer()

search_router = APIRouter(
    prefix="/search",
    tags=["Search"]
)

@search_router.get("/multilingual", status_code=status.HTTP_200_OK)
async def multilingual_search(
    query: str = Query(...),
    search_type: MultilingualSearchType = Query(default=MultilingualSearchType.HYBRID),
    text_id: Optional[str] = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100)
) -> MultilingualSearchResponse:

    return await get_multilingual_search_results(
        query=query,
        search_type=search_type.value,
        text_id=text_id,
        skip=skip,
        limit=limit
    )

@search_router.get("/chat/{pecha_segment_id}", status_code=status.HTTP_200_OK)
async def get_url_link(pecha_segment_id: str) -> SegmentLinkResponse:
    return await get_url_link_service(pecha_segment_id)


@search_router.get("/plans", status_code=status.HTTP_200_OK)
async def search_plans(
    authentication_credential: Annotated[
        HTTPAuthorizationCredentials, Depends(oauth2_scheme)
    ],
    tag: Annotated[Optional[str], Query()] = None,
    search: Annotated[Optional[str], Query()] = None,
    language: Annotated[Optional[str], Query()] = None,
    skip: Annotated[int, Query()] = 0,
    limit: Annotated[int, Query()] = 20,
) -> PlansResponse:
    return await get_filtered_plans(
        token=authentication_credential.credentials,
        search=search,
        sort_by="created_at",
        sort_order="desc",
        skip=skip,
        limit=limit,
        tag=tag,
        language=language,
    )