from typing import List, Set, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from pecha_api.plans.groups.groups_repository import (
    get_following_group_ids_by_user,
    get_groups_by_ids,
    get_public_group_ids,
)


def resolve_public_group_scope(
    *,
    db: Session,
    user_id: UUID,
    should_include_unfollowed: bool,
) -> Tuple[List[UUID], Set[UUID]]:
    """Return public group IDs to list and the user's followed public IDs."""
    followed_ids = get_following_group_ids_by_user(db=db, user_id=user_id)
    public_followed_ids = [
        group.id
        for group in get_groups_by_ids(db=db, group_ids=followed_ids)
        if group.is_public
    ]
    followed_set = set(public_followed_ids)

    if not should_include_unfollowed:
        return public_followed_ids, followed_set

    return get_public_group_ids(db=db), followed_set
