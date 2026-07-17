from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Tuple
from uuid import UUID

from pecha_api.group_recitation_collection.models import (
    GroupRecitationCollection,
    GroupRecitationCollectionItem,
)


def get_group_collections(
    db: Session,
    group_id: UUID,
    skip: int = 0,
    limit: int = 20,
) -> Tuple[List[GroupRecitationCollection], int]:
    """Get paginated collections for a group, excluding soft-deleted."""
    query = (
        db.query(GroupRecitationCollection)
        .filter(
            GroupRecitationCollection.group_id == group_id,
            GroupRecitationCollection.deleted_at.is_(None),
        )
        .order_by(GroupRecitationCollection.created_at.desc())
    )

    total = query.count()
    collections = query.offset(skip).limit(limit).all()

    return collections, total


def get_collection_by_id(
    db: Session,
    collection_id: UUID,
    group_id: UUID,
) -> Optional[GroupRecitationCollection]:
    """Get a single collection by ID and group_id, excluding soft-deleted."""
    return (
        db.query(GroupRecitationCollection)
        .filter(
            GroupRecitationCollection.id == collection_id,
            GroupRecitationCollection.group_id == group_id,
            GroupRecitationCollection.deleted_at.is_(None),
        )
        .first()
    )


def get_collection_items(
    db: Session,
    collection_id: UUID,
) -> List[GroupRecitationCollectionItem]:
    """Get all items for a collection, ordered by display_order, excluding soft-deleted."""
    return (
        db.query(GroupRecitationCollectionItem)
        .filter(
            GroupRecitationCollectionItem.group_recitation_collection_id == collection_id,
            GroupRecitationCollectionItem.deleted_at.is_(None),
        )
        .order_by(GroupRecitationCollectionItem.display_order)
        .all()
    )


def get_collection_item_counts(
    db: Session,
    collection_ids: List[UUID],
) -> dict:
    """Get item counts for multiple collections, excluding soft-deleted items."""
    if not collection_ids:
        return {}

    counts = (
        db.query(
            GroupRecitationCollectionItem.group_recitation_collection_id,
            func.count(GroupRecitationCollectionItem.id).label("count"),
        )
        .filter(
            GroupRecitationCollectionItem.group_recitation_collection_id.in_(collection_ids),
            GroupRecitationCollectionItem.deleted_at.is_(None),
        )
        .group_by(GroupRecitationCollectionItem.group_recitation_collection_id)
        .all()
    )

    return {row[0]: row[1] for row in counts}
