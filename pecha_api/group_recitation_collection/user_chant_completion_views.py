from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette import status

from pecha_api.group_recitation_collection.user_chant_completion_response_models import (
    CreateChantCompletionRequest,
    TodayChantCompletionsResponse,
    ChantCompletionDayCountResponse,
)
from pecha_api.group_recitation_collection.user_chant_completion_service import (
    get_today_completions_service,
    create_chant_completion_service,
    get_completion_day_count_service,
)

oauth2_scheme = HTTPBearer()

user_chant_completion_router = APIRouter(
    prefix="/users/me/groups/recitation-collections/{collection_id}/complete",
    tags=["User Chant Completion"],
)

# Legacy group-scoped routes kept for older app builds; the group_id is
# validated against the collection's owning group.
legacy_user_chant_completion_router = APIRouter(
    prefix="/users/me/groups/{group_id}/recitation-collections/{collection_id}/complete",
    tags=["User Chant Completion"],
)


@user_chant_completion_router.get(
    "/today",
    status_code=status.HTTP_200_OK,
)
def get_today_chant_completions(
    collection_id: UUID,
    authentication_credential: Annotated[
        HTTPAuthorizationCredentials, Depends(oauth2_scheme)
    ],
) -> TodayChantCompletionsResponse:
    """Get list of chants completed today by the authenticated user."""
    return get_today_completions_service(
        token=authentication_credential.credentials,
        collection_id=collection_id,
    )


@user_chant_completion_router.get(
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


@user_chant_completion_router.post(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
)
def create_chant_completion(
    collection_id: UUID,
    request: CreateChantCompletionRequest,
    authentication_credential: Annotated[
        HTTPAuthorizationCredentials, Depends(oauth2_scheme)
    ],
) -> None:
    """Log a chant completion for the authenticated user."""
    create_chant_completion_service(
        token=authentication_credential.credentials,
        collection_id=collection_id,
        chant_id=request.chant_id,
    )


@legacy_user_chant_completion_router.get(
    "/today",
    status_code=status.HTTP_200_OK,
)
def get_today_chant_completions_legacy(
    group_id: UUID,
    collection_id: UUID,
    authentication_credential: Annotated[
        HTTPAuthorizationCredentials, Depends(oauth2_scheme)
    ],
) -> TodayChantCompletionsResponse:
    """Get list of chants completed today by the authenticated user (group-scoped)."""
    return get_today_completions_service(
        token=authentication_credential.credentials,
        collection_id=collection_id,
        group_id=group_id,
    )


@legacy_user_chant_completion_router.get(
    "/days-count",
    status_code=status.HTTP_200_OK,
)
def get_chant_completion_day_count_legacy(
    group_id: UUID,
    collection_id: UUID,
    authentication_credential: Annotated[
        HTTPAuthorizationCredentials, Depends(oauth2_scheme)
    ],
) -> ChantCompletionDayCountResponse:
    """Get the number of unique days the user completed at least one chant in the collection (group-scoped)."""
    return get_completion_day_count_service(
        token=authentication_credential.credentials,
        collection_id=collection_id,
        group_id=group_id,
    )


@legacy_user_chant_completion_router.post(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
)
def create_chant_completion_legacy(
    group_id: UUID,
    collection_id: UUID,
    request: CreateChantCompletionRequest,
    authentication_credential: Annotated[
        HTTPAuthorizationCredentials, Depends(oauth2_scheme)
    ],
) -> None:
    """Log a chant completion for the authenticated user (group-scoped)."""
    create_chant_completion_service(
        token=authentication_credential.credentials,
        collection_id=collection_id,
        chant_id=request.chant_id,
        group_id=group_id,
    )
