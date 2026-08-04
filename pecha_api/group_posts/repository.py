from datetime import datetime, timezone
from typing import List, Optional, Sequence, Tuple
from uuid import UUID

from sqlalchemy.orm import Session, selectinload

from pecha_api.group_posts.enums import GroupPostStatus
from pecha_api.group_posts.models import GroupPost, GroupPostLink, GroupPostMedia


def get_group_posts(
    db: Session,
    group_id: UUID,
    skip: int = 0,
    limit: int = 20,
    status: Optional[GroupPostStatus] = None,
) -> Tuple[List[GroupPost], int]:
    """Get paginated posts for a group, newest first, excluding soft-deleted."""
    return get_posts_for_group_ids(
        db=db,
        group_ids=[group_id],
        skip=skip,
        limit=limit,
        status=status,
    )


def get_posts_for_group_ids(
    db: Session,
    group_ids: Sequence[UUID],
    skip: int = 0,
    limit: int = 20,
    status: Optional[GroupPostStatus] = None,
) -> Tuple[List[GroupPost], int]:
    """Get paginated published posts across groups, newest first."""
    if not group_ids:
        return [], 0

    query = db.query(GroupPost).filter(
        GroupPost.group_id.in_(group_ids),
        GroupPost.deleted_at.is_(None),
    )
    if status is not None:
        query = query.filter(GroupPost.status == status)

    query = query.order_by(GroupPost.published_at.desc(), GroupPost.id.desc())

    total = query.count()
    posts = (
        query.options(
            selectinload(GroupPost.media),
            selectinload(GroupPost.links),
        )
        .offset(skip)
        .limit(limit)
        .all()
    )

    return posts, total


def get_post_by_id(
    db: Session,
    post_id: UUID,
    group_id: UUID,
    status: Optional[GroupPostStatus] = None,
) -> Optional[GroupPost]:
    """Get a single post by ID and group_id, excluding soft-deleted."""
    query = (
        db.query(GroupPost)
        .options(
            selectinload(GroupPost.media),
            selectinload(GroupPost.links),
        )
        .filter(
            GroupPost.id == post_id,
            GroupPost.group_id == group_id,
            GroupPost.deleted_at.is_(None),
        )
    )
    if status is not None:
        query = query.filter(GroupPost.status == status)
    return query.first()


def create_post(db: Session, post: GroupPost) -> GroupPost:
    """Create a new post with its media and links."""
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


def update_post(db: Session, post: GroupPost) -> GroupPost:
    """Update an existing post."""
    db.commit()
    db.refresh(post)
    return post


def replace_post_media(
    db: Session,
    post: GroupPost,
    media: List[GroupPostMedia],
) -> GroupPost:
    """Replace the full media set of a post. The delete is emitted before the
    inserts so the (post_id, display_order) unique constraint cannot collide."""
    db.query(GroupPostMedia).filter(GroupPostMedia.post_id == post.id).delete()
    db.add_all(media)
    db.commit()
    db.refresh(post)
    return post


def replace_post_links(
    db: Session,
    post: GroupPost,
    links: List[GroupPostLink],
) -> GroupPost:
    """Replace the full link set of a post."""
    db.query(GroupPostLink).filter(GroupPostLink.post_id == post.id).delete()
    db.add_all(links)
    db.commit()
    db.refresh(post)
    return post


def soft_delete_post(db: Session, post: GroupPost, deleted_by: str) -> None:
    """Soft delete a post by setting deleted_at."""
    post.deleted_at = datetime.now(timezone.utc)
    post.deleted_by = deleted_by
    db.commit()
