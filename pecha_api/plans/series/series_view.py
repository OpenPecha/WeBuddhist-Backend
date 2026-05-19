from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette import status

from pecha_api.plans.series.series_response_models import CreateSeriesRequest, UpdateSeriesRequest, SeriesDTO
from pecha_api.plans.series.series_service import create_new_series, update_existing_series

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
