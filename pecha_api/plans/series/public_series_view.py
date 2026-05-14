from fastapi import APIRouter, Query
from typing import Optional
from uuid import UUID
from starlette import status

from pecha_api.plans.series.service_response_models import SeriesDTO, SeriesListResponse
from pecha_api.plans.series.series_service import get_filtered_series, get_series_detail


public_series_router = APIRouter(
    prefix="/series",
    tags=["Public Series"]
)


@public_series_router.get("", status_code=status.HTTP_200_OK, response_model=SeriesListResponse,
)
async def get_series_list(
    search: Optional[str] = Query(default=None, description="Search within serialized name JSON"),
    skip: int = Query(default=0),
    limit: int = Query(default=10),
):
    return await get_filtered_series(search=search, skip=skip, limit=limit)


@public_series_router.get("/{series_id}", status_code=status.HTTP_200_OK, response_model=SeriesDTO,
)
async def get_series(series_id: UUID):
    return get_series_detail(series_id=series_id)
