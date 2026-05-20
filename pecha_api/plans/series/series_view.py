from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette import status

from pecha_api.plans.series.series_response_models import CreateSeriesRequest, UpdateSeriesRequest, SeriesDTO, SeriesListResponse
from pecha_api.plans.series.series_service import create_new_series, update_existing_series, get_cms_filtered_series, get_cms_series_detail

oauth2_scheme = HTTPBearer()

cms_series_router = APIRouter(
    prefix="/cms/series",
    tags=["CMS Series"],
)


@cms_series_router.post("", status_code=status.HTTP_201_CREATED, response_model=SeriesDTO,
)
async def create_series(authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
                        create_series_request: CreateSeriesRequest):
    return create_new_series(
        token=authentication_credential.credentials,
        create_series_request=create_series_request
    )


@cms_series_router.put(
    "/{series_id}",
    status_code=status.HTTP_200_OK,
    response_model=SeriesDTO,
)
async def update_series(
    series_id: UUID,
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
    update_series_request: UpdateSeriesRequest,
):
    return update_existing_series(
        token=authentication_credential.credentials,
        series_id=series_id,
        update_series_request=update_series_request,
    )


@cms_series_router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=SeriesListResponse,
)
async def get_cms_series_list(
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
    search: Annotated[
        Optional[str], Query(description="Search within serialized name JSON")
    ] = None,
    skip: Annotated[int, Query()] = 0,
    limit: Annotated[int, Query()] = 10,
):
    return get_cms_filtered_series(
        token=authentication_credential.credentials,
        search=search,
        skip=skip,
        limit=limit,
    )


@cms_series_router.get(
    "/{series_id}",
    status_code=status.HTTP_200_OK,
    response_model=SeriesDTO,
)
async def get_cms_series(
    series_id: UUID,
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
):
    return get_cms_series_detail(
        token=authentication_credential.credentials,
        series_id=series_id,
    )