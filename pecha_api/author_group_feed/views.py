from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from starlette import status

from pecha_api.author_group_feed.response_models import AuthorGroupFeedResponse
from pecha_api.author_group_feed.service import get_author_group_feed_service
from pecha_api.db.database import get_db

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
async def get_author_group_feed(
    authentication_credential: Annotated[
        HTTPAuthorizationCredentials, Depends(oauth2_scheme)
    ],
    db: Annotated[Session, Depends(get_db)],
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    should_include_unfollowed: Annotated[
        bool,
        Query(
            alias="include_unfollowed",
            description=(
                "false = joined groups only (My tab); "
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

    Requires auth. Defaults to groups the user joined. Pass
    ``include_unfollowed=true`` to also mix in other public groups.
    """
    return await get_author_group_feed_service(
        db=db,
        token=authentication_credential.credentials,
        should_include_unfollowed=should_include_unfollowed,
        skip=skip,
        limit=limit,
        language=language,
    )
