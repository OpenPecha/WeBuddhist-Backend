from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette import status

from pecha_api.plans.users.recitation_collection.recitation_collection_completion_response_models import (
    CreateChantCompletionRequest,
    TodayChantCompletionsResponse,
    ChantCompletionDayCountResponse,
)
from pecha_api.plans.users.recitation_collection.recitation_collection_completion_service import (
    get_today_completions_service,
    create_chant_completion_service,
    get_completion_day_count_service,
)

oauth2_scheme = HTTPBearer()

recitation_collection_completion_router = APIRouter(
    prefix="/users/me/recitation-collections/{collection_id}/complete",
    tags=["Recitation Collection Chant Completion"],
)


@recitation_collection_completion_router.get(
    "/today",
    status_code=status.HTTP_200_OK,
)
def get_today_chant_completions(
    collection_id: UUID,
    authentication_credential: Annotated[
        HTTPAuthorizationCredentials, Depends(oauth2_scheme)
    ],
    x_timezone: Annotated[
        Optional[str],
        Header(alias="X-Timezone", description="IANA timezone for determining today's date."),
    ] = None,
) -> TodayChantCompletionsResponse:
    """Get list of chants completed today by the authenticated user."""
    return get_today_completions_service(
        token=authentication_credential.credentials,
        collection_id=collection_id,
        timezone_name=x_timezone,
    )


@recitation_collection_completion_router.get(
    "/days-count",
    status_code=status.HTTP_200_OK,
)
def get_chant_completion_day_count(
    collection_id: UUID,
    authentication_credential: Annotated[
        HTTPAuthorizationCredentials, Depends(oauth2_scheme)
    ],
) -> ChantCompletionDayCountResponse:
    """Get the number of unique days the user completed at least one chant in the collection."""
    return get_completion_day_count_service(
        token=authentication_credential.credentials,
        collection_id=collection_id,
    )


@recitation_collection_completion_router.post(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
)
def create_chant_completion(
    collection_id: UUID,
    request: CreateChantCompletionRequest,
    authentication_credential: Annotated[
        HTTPAuthorizationCredentials, Depends(oauth2_scheme)
    ],
    x_timezone: Annotated[
        Optional[str],
        Header(alias="X-Timezone", description="IANA timezone for determining today's date."),
    ] = None,
) -> None:
    """Log a chant completion for the authenticated user."""
    create_chant_completion_service(
        token=authentication_credential.credentials,
        collection_id=collection_id,
        chant_id=request.chant_id,
        timezone_name=x_timezone,
    )
