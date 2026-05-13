from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Query
from starlette import status

from pecha_api.plans.series.service_response_models import CreateSeriesRequest, SeriesDTO, SeriesListResponse
from pecha_api.plans.series.series_service import create_new_series, get_filtered_series, get_series_detail

cms_series_router = APIRouter(
    prefix="/cms/series",
    tags=["CMS Series"],
)


@cms_series_router.get("", status_code=status.HTTP_200_OK, response_model=SeriesListResponse,
)
async def get_series_list(
    search: Optional[str] = Query(default=None, description="Search within serialized name JSON"),
    skip: int = Query(default=0),
    limit: int = Query(default=10),
):
    return await get_filtered_series(search=search, skip=skip, limit=limit)


@cms_series_router.get("/{series_id}", status_code=status.HTTP_200_OK, response_model=SeriesDTO,
)
async def get_series(series_id: UUID):
    return get_series_detail(series_id=series_id)


@cms_series_router.post("", status_code=status.HTTP_201_CREATED, response_model=SeriesDTO,
)
async def create_series(create_series_request: CreateSeriesRequest):
    return create_new_series(create_series_request=create_series_request)
