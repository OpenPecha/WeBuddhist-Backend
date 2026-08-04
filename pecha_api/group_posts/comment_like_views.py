from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette import status

from pecha_api.group_posts.comment_like_response_models import (
    LikeCommentResponse,
    CommentLikersResponse,
)
from pecha_api.group_posts.comment_like_service import (
    like_comment_service,
    unlike_comment_service,
    list_comment_likers_service,
)
from pecha_api.plans.authors.plan_authors_service import validate_and_extract_author_details

oauth2_scheme = HTTPBearer()

public_group_post_comment_likes_router = APIRouter(
    prefix="/groups/author/comments/{comment_id}/likes",
    tags=["Public Group Post Comment Likes"],
)


@public_group_post_comment_likes_router.post(
    "",
    response_model=LikeCommentResponse,
)
def like_comment(
    comment_id: UUID,
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
    response: Response,
):
    """Like a comment (requires authentication). Returns 201 if newly created, 200 if already liked."""
    author = validate_and_extract_author_details(token=authentication_credential.credentials)
    result = like_comment_service(
        comment_id=comment_id,
        author_email=author.email,
    )
    response.status_code = status.HTTP_201_CREATED if result.is_new else status.HTTP_200_OK
    return result


@public_group_post_comment_likes_router.delete(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
)
def unlike_comment(
    comment_id: UUID,
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
):
    """Unlike a comment (requires authentication). Idempotent - succeeds even if not liked."""
    author = validate_and_extract_author_details(token=authentication_credential.credentials)
    unlike_comment_service(
        comment_id=comment_id,
        author_email=author.email,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@public_group_post_comment_likes_router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=CommentLikersResponse,
)
def list_comment_likers(
    comment_id: UUID,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """List users who liked a comment (public, no auth required)."""
    return list_comment_likers_service(
        comment_id=comment_id,
        skip=skip,
        limit=limit,
    )
