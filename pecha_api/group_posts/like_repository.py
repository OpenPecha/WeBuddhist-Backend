from typing import Dict, List, Optional, Set, Tuple
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from pecha_api.group_posts.like_models import GroupPostLike


def create_like(db: Session, like: GroupPostLike) -> Tuple[GroupPostLike, bool]:
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
            db.query(GroupPostLike)
            .options(selectinload(GroupPostLike.user))
            .filter(
                GroupPostLike.post_id == like.post_id,
                GroupPostLike.user_id == like.user_id,
            )
            .first()
        )
        return existing, False


def delete_like(db: Session, post_id: UUID, user_id: UUID) -> bool:
    """Delete a like. Returns True if deleted, False if didn't exist."""
    deleted_count = (
        db.query(GroupPostLike)
        .filter(
            GroupPostLike.post_id == post_id,
            GroupPostLike.user_id == user_id,
        )
        .delete()
    )
    db.commit()
    return deleted_count > 0


def get_like(db: Session, post_id: UUID, user_id: UUID) -> Optional[GroupPostLike]:
    """Get a specific like."""
    return (
        db.query(GroupPostLike)
        .options(selectinload(GroupPostLike.user))
        .filter(
            GroupPostLike.post_id == post_id,
            GroupPostLike.user_id == user_id,
        )
        .first()
    )


def like_exists(db: Session, post_id: UUID, user_id: UUID) -> bool:
    """Check if a like exists."""
    return (
        db.query(GroupPostLike)
        .filter(
            GroupPostLike.post_id == post_id,
            GroupPostLike.user_id == user_id,
        )
        .count()
        > 0
    )


def count_post_likes(db: Session, post_id: UUID) -> int:
    """Count likes for a single post."""
    return db.query(GroupPostLike).filter(GroupPostLike.post_id == post_id).count()


def get_post_likers(
    db: Session,
    post_id: UUID,
    skip: int = 0,
    limit: int = 20,
) -> Tuple[List[GroupPostLike], int]:
    """Get paginated likers for a post, newest first."""
    query = (
        db.query(GroupPostLike)
        .filter(GroupPostLike.post_id == post_id)
        .order_by(GroupPostLike.created_at.desc(), GroupPostLike.id.desc())
    )

    total = query.count()
    likes = (
        query.options(selectinload(GroupPostLike.user))
        .offset(skip)
        .limit(limit)
        .all()
    )

    return likes, total


def batch_count_post_likes(db: Session, post_ids: List[UUID]) -> Dict[UUID, int]:
    """Batch count likes for multiple posts. Returns dict of post_id -> count."""
    if not post_ids:
        return {}

    results = (
        db.query(GroupPostLike.post_id, func.count(GroupPostLike.id))
        .filter(GroupPostLike.post_id.in_(post_ids))
        .group_by(GroupPostLike.post_id)
        .all()
    )

    return {post_id: count for post_id, count in results}


# Alias used by feed enrichment helpers and tests.
get_like_counts_by_post_ids = batch_count_post_likes


def batch_check_posts_liked_by_user(
    db: Session, post_ids: List[UUID], user_id: UUID
) -> Set[UUID]:
    """Batch check which posts are liked by a user. Returns set of liked post_ids."""
    if not post_ids:
        return set()

    results = (
        db.query(GroupPostLike.post_id)
        .filter(
            GroupPostLike.post_id.in_(post_ids),
            GroupPostLike.user_id == user_id,
        )
        .all()
    )

    return {post_id for (post_id,) in results}
