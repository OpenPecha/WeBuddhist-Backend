from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette import status

from pecha_api.mantra.mantra_count_response_models import (
    MantraCountDetailDTO,
    MantraCountsResponse,
)
from pecha_api.mantra.mantra_count_service import (
    get_user_mantra_count_detail_service,
    get_user_mantra_counts_service,
)

oauth2_scheme = HTTPBearer()

user_mantra_count_router = APIRouter(
    prefix="/users/me/mantra-counts",
    tags=["Mantra Counts"],
)


@user_mantra_count_router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=MantraCountsResponse,
)
def get_user_mantra_counts(
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
    language: Annotated[
        Optional[str],
        Query(description="Language code for mantra title (e.g. 'en', 'bo', 'zh')"),
    ] = None,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records to return"),
) -> MantraCountsResponse:
    return get_user_mantra_counts_service(
        token=authentication_credential.credentials,
        language=language,
        skip=skip,
        limit=limit,
    )


@user_mantra_count_router.get(
    "/{mantra_id}",
    status_code=status.HTTP_200_OK,
    response_model=MantraCountDetailDTO,
)
def get_user_mantra_count_detail(
    mantra_id: UUID,
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
    language: Annotated[
        Optional[str],
        Query(description="Language code for mantra title (e.g. 'en', 'bo', 'zh')"),
    ] = None,
) -> MantraCountDetailDTO:
    return get_user_mantra_count_detail_service(
        token=authentication_credential.credentials,
        mantra_id=mantra_id,
        language=language,
    )
