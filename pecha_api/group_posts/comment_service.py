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

from pecha_api.group_posts.comment_models import GroupPostComment
from pecha_api.group_posts.comment_repository import (
    create_comment,
    get_comment_by_id,
    get_post_comments,
    soft_delete_comment,
)
from pecha_api.group_posts.comment_response_models import (
    GroupPostCommentDTO,
    GroupPostCommentsResponse,
)
from pecha_api.group_posts.repository import get_post_by_id

logger = logging.getLogger(__name__)


def _isoformat(value) -> Optional[str]:
    if value is None:
        return None
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def build_comment_dto(comment: GroupPostComment) -> GroupPostCommentDTO:
    """Build a comment DTO with user email."""
    user_email = comment.user.email if comment.user else "unknown@example.com"
    return GroupPostCommentDTO(
        id=comment.id,
        post_id=comment.post_id,
        user_id=comment.user_id,
        user_email=user_email,
        text=comment.text,
        created_at=_isoformat(comment.created_at),
        updated_at=_isoformat(comment.updated_at),
    )


def _validate_group_is_public(db: Session, group_id: UUID) -> None:
    """Validate that group exists and is public."""
    group = get_group_by_id(db=db, group_id=group_id)
    if not group or not group.is_public:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=NOT_FOUND,
        )


def _validate_post_published(db: Session, post_id: UUID, group_id: UUID) -> None:
    """Validate that post exists, is published, and not soft-deleted."""
    post = get_post_by_id(db=db, post_id=post_id, group_id=group_id, status=None)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=NOT_FOUND,
        )


def list_post_comments_service(
    group_id: UUID,
    post_id: UUID,
    skip: int = 0,
    limit: int = 20,
) -> GroupPostCommentsResponse:
    """Public list of comments on a post."""
    with SessionLocal() as db:
        _validate_group_is_public(db, group_id)
        _validate_post_published(db, post_id, group_id)

        comments, total = get_post_comments(
            db=db,
            post_id=post_id,
            skip=skip,
            limit=limit,
        )

        return GroupPostCommentsResponse(
            comments=[build_comment_dto(comment) for comment in comments],
            skip=skip,
            limit=limit,
            total=total,
        )


def create_post_comment_service(
    group_id: UUID,
    post_id: UUID,
    author_email: str,
    text: str,
) -> GroupPostCommentDTO:
    """Create a comment on a post. User must be authenticated."""
    with SessionLocal() as db:
        _validate_group_is_public(db, group_id)
        _validate_post_published(db, post_id, group_id)

        # Look up user by email in Users table
        user = db.query(Users).filter(Users.email == author_email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"User account not found: {author_email}",
            )

        comment = GroupPostComment(
            post_id=post_id,
            user_id=user.id,
            text=text,
        )

        created = create_comment(db=db, comment=comment)
        return build_comment_dto(created)


def delete_post_comment_service(
    group_id: UUID,
    post_id: UUID,
    comment_id: UUID,
    user_id: UUID,
) -> None:
    """Delete a comment. User must be the author or the post author."""
    with SessionLocal() as db:
        _validate_group_is_public(db, group_id)
        _validate_post_published(db, post_id, group_id)

        comment = get_comment_by_id(db=db, comment_id=comment_id, post_id=post_id)
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=NOT_FOUND,
            )

        if comment.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own comments",
            )

        soft_delete_comment(db=db, comment=comment)
