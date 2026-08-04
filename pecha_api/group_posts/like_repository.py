from typing import Dict, List
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from pecha_api.group_posts.like_models import GroupPostLike


def get_like_counts_by_post_ids(
    db: Session,
    post_ids: List[UUID],
) -> Dict[UUID, int]:
    """Return like counts keyed by post_id for the given posts."""
    if not post_ids:
        return {}

    rows = (
        db.query(GroupPostLike.post_id, func.count(GroupPostLike.id))
        .filter(GroupPostLike.post_id.in_(post_ids))
        .group_by(GroupPostLike.post_id)
        .all()
    )
    return {post_id: count for post_id, count in rows}
