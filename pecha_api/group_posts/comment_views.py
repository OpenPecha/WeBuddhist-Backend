from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette import status

from pecha_api.group_posts.comment_response_models import (
    CreateGroupPostCommentRequest,
    GroupPostCommentDTO,
    GroupPostCommentsResponse,
)
from pecha_api.group_posts.comment_service import (
    create_post_comment_service,
    delete_post_comment_service,
    list_post_comments_service,
)
from pecha_api.plans.authors.plan_authors_service import validate_and_extract_author_details

oauth2_scheme = HTTPBearer()

public_group_post_comments_router = APIRouter(
    prefix="/author/groups/{group_id}/posts/{post_id}/comments",
    tags=["Public Group Post Comments"],
)


@public_group_post_comments_router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=GroupPostCommentsResponse,
)
def list_post_comments(
    group_id: UUID,
    post_id: UUID,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """List comments on a post (newest first)."""
    return list_post_comments_service(
        group_id=group_id,
        post_id=post_id,
        skip=skip,
        limit=limit,
    )


@public_group_post_comments_router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=GroupPostCommentDTO,
)
def create_post_comment(
    group_id: UUID,
    post_id: UUID,
    request: CreateGroupPostCommentRequest,
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
):
    """Create a comment on a post (requires authentication)."""
    author = validate_and_extract_author_details(token=authentication_credential.credentials)
    return create_post_comment_service(
        group_id=group_id,
        post_id=post_id,
        user_id=author.id,
        text=request.text,
    )


@public_group_post_comments_router.delete(
    "/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_post_comment(
    group_id: UUID,
    post_id: UUID,
    comment_id: UUID,
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
):
    """Delete a comment (only the author can delete)."""
    author = validate_and_extract_author_details(token=authentication_credential.credentials)
    delete_post_comment_service(
        group_id=group_id,
        post_id=post_id,
        comment_id=comment_id,
        user_id=author.id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
