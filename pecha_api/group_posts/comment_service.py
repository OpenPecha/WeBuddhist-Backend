import logging
from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session
from starlette import status

from pecha_api.config import get
from pecha_api.db.database import SessionLocal
from pecha_api.plans.groups.groups_repository import get_group_by_id
from pecha_api.plans.response_message import NOT_FOUND
from pecha_api.uploads.S3_utils import generate_presigned_access_url
from pecha_api.users.users_models import Users

from pecha_api.group_posts.comment_models import GroupPostComment
from pecha_api.group_posts.comment_repository import (
    create_comment,
    get_comment_by_id,
    get_comment_by_id_only,
    get_post_comments,
    soft_delete_comment,
)
from pecha_api.group_posts.comment_response_models import (
    GroupPostCommentDTO,
    GroupPostCommentUserDTO,
    GroupPostCommentsResponse,
)
from pecha_api.group_posts.repository import get_post_by_id, get_post_by_id_only
from pecha_api.group_posts.comment_like_repository import (
    batch_count_comment_likes,
    batch_check_comments_liked_by_user,
    count_comment_likes,
    like_exists,
)

logger = logging.getLogger(__name__)


def _isoformat(value) -> Optional[str]:
    if value is None:
        return None
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def _generate_avatar_url(avatar_key: Optional[str]) -> Optional[str]:
    if not avatar_key:
        return None
    try:
        return generate_presigned_access_url(
            bucket_name=get("AWS_BUCKET_NAME"),
            s3_key=avatar_key,
        )
    except Exception:
        logger.exception("Failed to generate comment user avatar URL")
        return None


def _build_comment_user(user: Optional[Users]) -> GroupPostCommentUserDTO:
    if not user:
        return GroupPostCommentUserDTO(
            first_name="Unknown",
            email="unknown@example.com",
        )
    return GroupPostCommentUserDTO(
        first_name=user.firstname,
        last_name=user.lastname,
        email=user.email,
        avatar_url=_generate_avatar_url(user.avatar_url),
    )


def build_comment_dto(
    comment: GroupPostComment,
    like_count: int = 0,
    liked_by_me: bool = False,
) -> GroupPostCommentDTO:
    """Build a comment DTO with public user details."""
    comment_user = _build_comment_user(comment.user)
    return GroupPostCommentDTO(
        id=comment.id,
        post_id=comment.post_id,
        parent_comment_id=comment.parent_comment_id,
        user_email=comment_user.email,
        user=comment_user,
        text=comment.text,
        created_at=_isoformat(comment.created_at),
        updated_at=_isoformat(comment.updated_at),
        like_count=like_count,
        liked_by_me=liked_by_me,
    )


def _validate_group_is_public(db: Session, group_id: UUID) -> None:
    """Validate that group exists and is public."""
    group = get_group_by_id(db=db, group_id=group_id)
    if not group or not group.is_public:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=NOT_FOUND,
        )


def _get_and_validate_post(db: Session, post_id: UUID) -> tuple:
    """Get post and validate it exists. Returns (post, group_id)."""
    post = get_post_by_id_only(db=db, post_id=post_id, status=None)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=NOT_FOUND,
        )
    return post, post.group_id


def list_post_comments_service(
    post_id: UUID,
    skip: int = 0,
    limit: int = 20,
    user_id: Optional[UUID] = None,
) -> GroupPostCommentsResponse:
    """Public list of comments on a post."""
    with SessionLocal() as db:
        post, group_id = _get_and_validate_post(db, post_id)
        _validate_group_is_public(db, group_id)

        comments, total = get_post_comments(
            db=db,
            post_id=post_id,
            skip=skip,
            limit=limit,
        )

        # Batch hydrate like counts and liked_by_me
        comment_ids = [comment.id for comment in comments]
        like_counts = batch_count_comment_likes(db=db, comment_ids=comment_ids)
        liked_comments = (
            batch_check_comments_liked_by_user(db=db, comment_ids=comment_ids, user_id=user_id)
            if user_id
            else set()
        )

        return GroupPostCommentsResponse(
            comments=[
                build_comment_dto(
                    comment,
                    like_count=like_counts.get(comment.id, 0),
                    liked_by_me=comment.id in liked_comments,
                )
                for comment in comments
            ],
            skip=skip,
            limit=limit,
            total=total,
        )


def create_post_comment_service(
    post_id: UUID,
    user_id: UUID,
    text: str,
    parent_comment_id: Optional[UUID] = None,
) -> GroupPostCommentDTO:
    """Create a top-level comment or a reply to any comment on the post."""
    with SessionLocal() as db:
        post, group_id = _get_and_validate_post(db, post_id)
        _validate_group_is_public(db, group_id)

        if parent_comment_id is not None:
            parent_comment = get_comment_by_id(
                db=db,
                comment_id=parent_comment_id,
                post_id=post_id,
            )
            if not parent_comment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Parent comment not found",
                )

        comment = GroupPostComment(
            post_id=post_id,
            user_id=user_id,
            parent_comment_id=parent_comment_id,
            text=text,
        )

        created = create_comment(db=db, comment=comment)
        return build_comment_dto(created)


def delete_post_comment_service(
    comment_id: UUID,
    user_id: UUID,
) -> None:
    """Delete a comment. User must be the author or the post author."""
    with SessionLocal() as db:
        comment = get_comment_by_id_only(db=db, comment_id=comment_id)
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=NOT_FOUND,
            )

        # Validate post and group
        post, group_id = _get_and_validate_post(db, comment.post_id)
        _validate_group_is_public(db, group_id)

        if comment.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own comments",
            )

        soft_delete_comment(db=db, comment=comment)
