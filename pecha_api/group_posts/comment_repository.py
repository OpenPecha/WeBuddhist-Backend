from datetime import datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session, selectinload

from pecha_api.group_posts.comment_models import GroupPostComment


def get_post_comments(
    db: Session,
    post_id: UUID,
    skip: int = 0,
    limit: int = 20,
) -> Tuple[List[GroupPostComment], int]:
    """Get paginated comments for a post, newest first, excluding soft-deleted."""
    query = (
        db.query(GroupPostComment)
        .filter(
            GroupPostComment.post_id == post_id,
            GroupPostComment.deleted_at.is_(None),
        )
        .order_by(GroupPostComment.created_at.desc(), GroupPostComment.id.desc())
    )

    total = query.count()
    comments = (
        query.options(
            selectinload(GroupPostComment.user),
        )
        .offset(skip)
        .limit(limit)
        .all()
    )

    return comments, total


def get_comment_by_id(
    db: Session,
    comment_id: UUID,
    post_id: UUID,
) -> Optional[GroupPostComment]:
    """Get a single comment by ID and post_id, excluding soft-deleted."""
    return (
        db.query(GroupPostComment)
        .options(selectinload(GroupPostComment.user))
        .filter(
            GroupPostComment.id == comment_id,
            GroupPostComment.post_id == post_id,
            GroupPostComment.deleted_at.is_(None),
        )
        .first()
    )


def create_comment(db: Session, comment: GroupPostComment) -> GroupPostComment:
    """Create a new comment."""
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def soft_delete_comment(db: Session, comment: GroupPostComment) -> None:
    """Soft delete a comment."""
    comment.deleted_at = datetime.now(timezone.utc)
    db.commit()
