from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette import status

from pecha_api.author_group_feed.response_models import AuthorGroupFeedResponse
from pecha_api.author_group_feed.service import get_author_group_feed_service

oauth2_scheme = HTTPBearer()

author_group_feed_router = APIRouter(
    prefix="/author/groups/feeds",
    tags=["Public Author Groups"],
)


@author_group_feed_router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=AuthorGroupFeedResponse,
)
def get_author_group_feed(
    authentication_credential: Annotated[
        HTTPAuthorizationCredentials, Depends(oauth2_scheme)
    ],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    include_unfollowed: Annotated[
        bool,
        Query(
            description=(
                "false = followed groups only (My tab); "
                "true = also mix in other public groups (Discover tab)"
            ),
        ),
    ] = False,
    language: Annotated[
        Optional[str],
        Query(description="Preferred language for event metadata"),
    ] = None,
):
    """Mixed chronological feed of posts and events from author groups.

    Requires auth. Defaults to groups the user follows. Pass
    ``include_unfollowed=true`` to also mix in other public groups.
    """
    return get_author_group_feed_service(
        token=authentication_credential.credentials,
        include_unfollowed=include_unfollowed,
        skip=skip,
        limit=limit,
        language=language,
    )
