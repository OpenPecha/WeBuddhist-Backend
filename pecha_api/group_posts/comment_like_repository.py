from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Tuple
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from pecha_api.group_posts.comment_like_models import GroupPostCommentLike


def create_like(db: Session, like: GroupPostCommentLike) -> Tuple[GroupPostCommentLike, bool]:
    """Create a new like. Returns (like, created) where created=True if new, False if already existed."""
    try:
        db.add(like)
        db.commit()
        db.refresh(like)
        return like, True
    except IntegrityError:
        db.rollback()
        # Already liked - fetch existing
        existing = (
            db.query(GroupPostCommentLike)
            .options(selectinload(GroupPostCommentLike.user))
            .filter(
                GroupPostCommentLike.comment_id == like.comment_id,
                GroupPostCommentLike.user_id == like.user_id,
            )
            .first()
        )
        return existing, False


def delete_like(db: Session, comment_id: UUID, user_id: UUID) -> bool:
    """Delete a like. Returns True if deleted, False if didn't exist."""
    deleted_count = (
        db.query(GroupPostCommentLike)
        .filter(
            GroupPostCommentLike.comment_id == comment_id,
            GroupPostCommentLike.user_id == user_id,
        )
        .delete()
    )
    db.commit()
    return deleted_count > 0


def get_like(db: Session, comment_id: UUID, user_id: UUID) -> Optional[GroupPostCommentLike]:
    """Get a specific like."""
    return (
        db.query(GroupPostCommentLike)
        .options(selectinload(GroupPostCommentLike.user))
        .filter(
            GroupPostCommentLike.comment_id == comment_id,
            GroupPostCommentLike.user_id == user_id,
        )
        .first()
    )


def like_exists(db: Session, comment_id: UUID, user_id: UUID) -> bool:
    """Check if a like exists."""
    return (
        db.query(GroupPostCommentLike)
        .filter(
            GroupPostCommentLike.comment_id == comment_id,
            GroupPostCommentLike.user_id == user_id,
        )
        .count()
        > 0
    )


def count_comment_likes(db: Session, comment_id: UUID) -> int:
    """Count likes for a single comment."""
    return db.query(GroupPostCommentLike).filter(GroupPostCommentLike.comment_id == comment_id).count()


def get_comment_likers(
    db: Session,
    comment_id: UUID,
    skip: int = 0,
    limit: int = 20,
) -> Tuple[List[GroupPostCommentLike], int]:
    """Get paginated likers for a comment, newest first."""
    query = (
        db.query(GroupPostCommentLike)
        .filter(GroupPostCommentLike.comment_id == comment_id)
        .order_by(GroupPostCommentLike.created_at.desc(), GroupPostCommentLike.id.desc())
    )

    total = query.count()
    likes = (
        query.options(selectinload(GroupPostCommentLike.user))
        .offset(skip)
        .limit(limit)
        .all()
    )

    return likes, total


def batch_count_comment_likes(db: Session, comment_ids: List[UUID]) -> Dict[UUID, int]:
    """Batch count likes for multiple comments. Returns dict of comment_id -> count."""
    if not comment_ids:
        return {}

    results = (
        db.query(GroupPostCommentLike.comment_id, func.count(GroupPostCommentLike.id))
        .filter(GroupPostCommentLike.comment_id.in_(comment_ids))
        .group_by(GroupPostCommentLike.comment_id)
        .all()
    )

    return {comment_id: count for comment_id, count in results}


def batch_check_comments_liked_by_user(
    db: Session, comment_ids: List[UUID], user_id: UUID
) -> Set[UUID]:
    """Batch check which comments are liked by a user. Returns set of liked comment_ids."""
    if not comment_ids:
        return set()

    results = (
        db.query(GroupPostCommentLike.comment_id)
        .filter(
            GroupPostCommentLike.comment_id.in_(comment_ids),
            GroupPostCommentLike.user_id == user_id,
        )
        .all()
    )

    return {comment_id for (comment_id,) in results}
