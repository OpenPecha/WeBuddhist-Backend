import logging
from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session
from starlette import status

from pecha_api.db.database import SessionLocal
from pecha_api.plans.groups.groups_repository import get_group_by_id
from pecha_api.plans.response_message import NOT_FOUND
from pecha_api.users.users_models import Users

from pecha_api.group_posts.comment_like_models import GroupPostCommentLike
from pecha_api.group_posts.comment_like_repository import (
    create_like,
    delete_like,
    get_comment_likers,
    count_comment_likes,
)
from pecha_api.group_posts.comment_like_response_models import (
    LikeCommentResponse,
    CommentLikerDTO,
    CommentLikersResponse,
)
from pecha_api.group_posts.comment_repository import get_comment_by_id_only
from pecha_api.group_posts.repository import get_post_by_id_only
from pecha_api.group_posts.service_utils import (
    isoformat,
    validate_group_is_public,
)

logger = logging.getLogger(__name__)


def _get_and_validate_comment(db: Session, comment_id: UUID) -> tuple:
    """Get comment and validate hierarchy. Returns (comment, post, group_id)."""
    comment = get_comment_by_id_only(db=db, comment_id=comment_id)
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=NOT_FOUND,
        )
    
    post = get_post_by_id_only(db=db, post_id=comment.post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=NOT_FOUND,
        )
    
    return comment, post, post.group_id


def like_comment_service(
    comment_id: UUID,
    user_id: UUID,
) -> LikeCommentResponse:
    """Like a comment. Idempotent - returns 200 if already liked."""
    with SessionLocal() as db:
        comment, post, group_id = _get_and_validate_comment(db, comment_id)
        validate_group_is_public(db, group_id)

        like = GroupPostCommentLike(
            comment_id=comment_id,
            user_id=user_id,
        )

        created_like, is_new = create_like(db=db, like=like)
        like_count = count_comment_likes(db=db, comment_id=comment_id)

        return LikeCommentResponse(
            comment_id=comment_id,
            user_id=user_id,
            liked=True,
            like_count=like_count,
            created_at=isoformat(created_like.created_at),
            is_new=is_new,
        )


def unlike_comment_service(
    comment_id: UUID,
    user_id: UUID,
) -> None:
    """Unlike a comment. Idempotent - succeeds even if not liked."""
    with SessionLocal() as db:
        comment, post, group_id = _get_and_validate_comment(db, comment_id)
        validate_group_is_public(db, group_id)

        delete_like(db=db, comment_id=comment_id, user_id=user_id)


def list_comment_likers_service(
    comment_id: UUID,
    skip: int = 0,
    limit: int = 20,
) -> CommentLikersResponse:
    """Public list of users who liked a comment."""
    with SessionLocal() as db:
        comment, post, group_id = _get_and_validate_comment(db, comment_id)
        validate_group_is_public(db, group_id)

        likes, total = get_comment_likers(
            db=db,
            comment_id=comment_id,
            skip=skip,
            limit=limit,
        )

        return CommentLikersResponse(
            likes=[
                CommentLikerDTO(
                    user_id=like.user_id,
                    user_email=like.user.email if like.user else "unknown@example.com",
                    created_at=isoformat(like.created_at),
                )
                for like in likes
            ],
            skip=skip,
            limit=limit,
            total=total,
        )
