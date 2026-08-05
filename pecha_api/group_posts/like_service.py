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

from pecha_api.group_posts.enums import GroupPostStatus
from pecha_api.group_posts.like_models import GroupPostLike
from pecha_api.group_posts.like_repository import (
    create_like,
    delete_like,
    get_post_likers,
    count_post_likes,
)
from pecha_api.group_posts.like_response_models import (
    LikePostResponse,
    PostLikerDTO,
    PostLikersResponse,
)
from pecha_api.group_posts.repository import get_post_by_id_only
from pecha_api.group_posts.service_utils import (
    isoformat,
    validate_group_is_public,
    resolve_user_id,
)

logger = logging.getLogger(__name__)


def _get_and_validate_post(db: Session, post_id: UUID) -> tuple:
    """Get post and validate it exists, is published, and not soft-deleted. Returns (post, group_id)."""
    post = get_post_by_id_only(db=db, post_id=post_id, status=GroupPostStatus.PUBLISHED)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=NOT_FOUND,
        )
    return post, post.group_id


def like_post_service(
    post_id: UUID,
    author_email: str,
) -> LikePostResponse:
    """Like a post. Idempotent - returns 200 if already liked."""
    with SessionLocal() as db:
        post, group_id = _get_and_validate_post(db, post_id)
        validate_group_is_public(db, group_id)

        user_id = resolve_user_id(db, author_email)

        like = GroupPostLike(
            post_id=post_id,
            user_id=user_id,
        )

        created_like, is_new = create_like(db=db, like=like)
        like_count = count_post_likes(db=db, post_id=post_id)

        return LikePostResponse(
            post_id=post_id,
            user_id=user_id,
            liked=True,
            like_count=like_count,
            created_at=isoformat(created_like.created_at),
            is_new=is_new,
        )


def unlike_post_service(
    post_id: UUID,
    author_email: str,
) -> None:
    """Unlike a post. Idempotent - succeeds even if not liked."""
    with SessionLocal() as db:
        post, group_id = _get_and_validate_post(db, post_id)
        validate_group_is_public(db, group_id)

        user_id = resolve_user_id(db, author_email)

        delete_like(db=db, post_id=post_id, user_id=user_id)


def list_post_likers_service(
    post_id: UUID,
    skip: int = 0,
    limit: int = 20,
) -> PostLikersResponse:
    """Public list of users who liked a post."""
    with SessionLocal() as db:
        post, group_id = _get_and_validate_post(db, post_id)
        validate_group_is_public(db, group_id)

        likes, total = get_post_likers(
            db=db,
            post_id=post_id,
            skip=skip,
            limit=limit,
        )

        return PostLikersResponse(
            likes=[
                PostLikerDTO(
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
