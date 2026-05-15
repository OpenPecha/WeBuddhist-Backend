from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette import status

from pecha_api.plans.series.service_response_models import CreateSeriesRequest, SeriesDTO
from pecha_api.plans.series.series_service import create_new_series

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
