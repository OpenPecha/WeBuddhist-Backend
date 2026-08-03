from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette import status

from .location_response_models import (
    CreateLocationRequest,
    LocationDetailDTO,
    LocationsResponse,
    UpdateLocationRequest,
)
from .location_service import (
    create_location_service,
    delete_location_service,
    get_location_by_id_service,
    get_locations_service,
    update_location_service,
)

oauth2_scheme = HTTPBearer()

cms_locations_router = APIRouter(
    prefix="/cms/author/groups/{group_id}/locations",
    tags=["CMS Locations"],
)


@cms_locations_router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=LocationsResponse,
)
def get_locations_endpoint(
    group_id: UUID,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
    search: Annotated[Optional[str], Query(description="Filter locations by name")] = None,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> LocationsResponse:
    return get_locations_service(
        token=credentials.credentials,
        group_id=group_id,
        search=search,
        skip=skip,
        limit=limit,
    )


@cms_locations_router.get(
    "/{location_id}",
    status_code=status.HTTP_200_OK,
    response_model=LocationDetailDTO,
)
def get_location_by_id_endpoint(
    group_id: UUID,
    location_id: UUID,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
) -> LocationDetailDTO:
    return get_location_by_id_service(
        token=credentials.credentials,
        group_id=group_id,
        location_id=location_id,
    )


@cms_locations_router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=LocationDetailDTO,
)
def create_location_endpoint(
    group_id: UUID,
    request: CreateLocationRequest,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
) -> LocationDetailDTO:
    return create_location_service(
        token=credentials.credentials,
        group_id=group_id,
        request=request,
    )


@cms_locations_router.patch(
    "/{location_id}",
    status_code=status.HTTP_200_OK,
    response_model=LocationDetailDTO,
)
def update_location_endpoint(
    group_id: UUID,
    location_id: UUID,
    request: UpdateLocationRequest,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
) -> LocationDetailDTO:
    return update_location_service(
        token=credentials.credentials,
        group_id=group_id,
        location_id=location_id,
        request=request,
    )


@cms_locations_router.delete(
    "/{location_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_location_endpoint(
    group_id: UUID,
    location_id: UUID,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
) -> None:
    delete_location_service(
        token=credentials.credentials,
        group_id=group_id,
        location_id=location_id,
    )
