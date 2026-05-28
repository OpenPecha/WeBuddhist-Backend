from fastapi import APIRouter, Query
from typing import Optional, Annotated
from uuid import UUID
from starlette import status

from pecha_api.plans.series.series_response_models import SeriesDTO, SeriesListResponse
from pecha_api.plans.series.series_service import get_filtered_series, get_series_detail


public_series_router = APIRouter(prefix="/series", tags=["Public Series"])


@public_series_router.get(
    "", status_code=status.HTTP_200_OK, response_model=SeriesListResponse
)
async def get_series_list(
    search: Annotated[
        Optional[str], Query(description="Search within serialized name JSON")
    ] = None,
    language: Annotated[
        Optional[str],
        Query(description="Filter by series metadata language (e.g. 'en', 'bo', 'zh')"),
    ] = None,
    group_id: Annotated[
        Optional[UUID],
        Query(description="Filter by author group id"),
    ] = None,
    skip: Annotated[int, Query()] = 0,
    limit: Annotated[int, Query()] = 10,
):
    return get_filtered_series(search=search, skip=skip, limit=limit, language=language, group_id=group_id)


@public_series_router.get(
    "/{series_id}", status_code=status.HTTP_200_OK, response_model=SeriesDTO
)
async def get_series(series_id: UUID):
    return get_series_detail(series_id=series_id)
