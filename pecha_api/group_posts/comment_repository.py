from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from pecha_api.group_posts.comment_models import GroupPostComment


def get_comment_counts_by_post_ids(
    db: Session,
    post_ids: List[UUID],
) -> Dict[UUID, int]:
    """Return non-deleted comment counts keyed by post_id."""
    if not post_ids:
        return {}

    rows = (
        db.query(GroupPostComment.post_id, func.count(GroupPostComment.id))
        .filter(
            GroupPostComment.post_id.in_(post_ids),
            GroupPostComment.deleted_at.is_(None),
        )
        .group_by(GroupPostComment.post_id)
        .all()
    )
    return {post_id: count for post_id, count in rows}


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
