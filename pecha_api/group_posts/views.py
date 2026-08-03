from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette import status

from pecha_api.group_posts.response_models import GroupPostDTO, GroupPostsResponse
from pecha_api.group_posts.service import (
    get_group_post_detail_service,
    list_group_posts_service,
)
from pecha_api.plans.authors.plan_authors_service import validate_and_extract_author_details
from pecha_api.users.users_models import Users
from pecha_api.db.database import SessionLocal

oauth2_scheme_optional = HTTPBearer(auto_error=False)

public_group_posts_router = APIRouter(
    prefix="/author/groups/{group_id}/posts",
    tags=["Public Group Posts"],
)


@public_group_posts_router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=GroupPostsResponse,
)
def list_group_posts(
    group_id: UUID,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    authentication_credential: Annotated[
        Optional[HTTPAuthorizationCredentials], Depends(oauth2_scheme_optional)
    ] = None,
):
    """Chronological feed of published posts for a public group. Optional auth for liked_by_me."""
    user_id = None
    if authentication_credential:
        try:
            author = validate_and_extract_author_details(token=authentication_credential.credentials)
            with SessionLocal() as db:
                user = db.query(Users).filter(Users.email == author.email).first()
                if user:
                    user_id = user.id
        except Exception:
            pass
    return list_group_posts_service(group_id=group_id, skip=skip, limit=limit, user_id=user_id)


@public_group_posts_router.get(
    "/{post_id}",
    status_code=status.HTTP_200_OK,
    response_model=GroupPostDTO,
)
def get_group_post_detail(
    group_id: UUID,
    post_id: UUID,
    authentication_credential: Annotated[
        Optional[HTTPAuthorizationCredentials], Depends(oauth2_scheme_optional)
    ] = None,
):
    """Get a published post with presigned media URLs. Optional auth for liked_by_me."""
    user_id = None
    if authentication_credential:
        try:
            author = validate_and_extract_author_details(token=authentication_credential.credentials)
            with SessionLocal() as db:
                user = db.query(Users).filter(Users.email == author.email).first()
                if user:
                    user_id = user.id
        except Exception:
            pass
    return get_group_post_detail_service(group_id=group_id, post_id=post_id, user_id=user_id)
