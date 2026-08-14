from datetime import datetime, timezone
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


def get_collections_by_group_ids(
    db: Session,
    group_ids: List[UUID],
) -> List[GroupRecitationCollection]:
    """Get all non-deleted collections for the given groups, newest first."""
    if not group_ids:
        return []

    return (
        db.query(GroupRecitationCollection)
        .filter(
            GroupRecitationCollection.group_id.in_(group_ids),
            GroupRecitationCollection.deleted_at.is_(None),
        )
        .order_by(GroupRecitationCollection.created_at.desc())
        .all()
    )


def get_collections_for_group_ids_with_total(
    db: Session,
    group_ids: List[UUID],
    limit: int,
) -> Tuple[List[GroupRecitationCollection], int]:
    """Get non-deleted collections for the given groups, newest first, with total count."""
    if not group_ids:
        return [], 0

    query = db.query(GroupRecitationCollection).filter(
        GroupRecitationCollection.group_id.in_(group_ids),
        GroupRecitationCollection.deleted_at.is_(None),
    )
    total = query.count()
    collections = query.order_by(
        GroupRecitationCollection.created_at.desc(), GroupRecitationCollection.id.desc()
    ).limit(limit).all()
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


def create_collection(
    db: Session,
    collection: GroupRecitationCollection,
) -> GroupRecitationCollection:
    """Create a new collection."""
    db.add(collection)
    db.commit()
    db.refresh(collection)
    return collection


def update_collection(
    db: Session,
    collection: GroupRecitationCollection,
) -> GroupRecitationCollection:
    """Update an existing collection."""
    db.commit()
    db.refresh(collection)
    return collection


def soft_delete_collection(
    db: Session,
    collection: GroupRecitationCollection,
) -> None:
    """Soft delete a collection by setting deleted_at."""
    collection.deleted_at = datetime.now(timezone.utc)
    db.commit()


def get_max_display_order(
    db: Session,
    collection_id: UUID,
) -> int:
    """Get the maximum display_order for items in a collection."""
    result = (
        db.query(func.max(GroupRecitationCollectionItem.display_order))
        .filter(
            GroupRecitationCollectionItem.group_recitation_collection_id == collection_id,
            GroupRecitationCollectionItem.deleted_at.is_(None),
        )
        .scalar()
    )
    return result or 0


def create_collection_items(
    db: Session,
    items: List[GroupRecitationCollectionItem],
) -> List[GroupRecitationCollectionItem]:
    """Create multiple collection items."""
    db.add_all(items)
    db.commit()
    for item in items:
        db.refresh(item)
    return items


def soft_delete_collection_item(
    db: Session,
    item: GroupRecitationCollectionItem,
) -> None:
    """Soft delete a collection item."""
    item.deleted_at = datetime.now(timezone.utc)
    db.commit()


def get_collection_item_by_id(
    db: Session,
    item_id: UUID,
    collection_id: UUID,
) -> Optional[GroupRecitationCollectionItem]:
    """Get a single item by ID and collection_id, excluding soft-deleted."""
    return (
        db.query(GroupRecitationCollectionItem)
        .filter(
            GroupRecitationCollectionItem.id == item_id,
            GroupRecitationCollectionItem.group_recitation_collection_id == collection_id,
            GroupRecitationCollectionItem.deleted_at.is_(None),
        )
        .first()
    )


def update_item_display_orders(
    db: Session,
    items: List[GroupRecitationCollectionItem],
) -> None:
    """Update display_order for multiple items."""
    db.commit()


def get_collection_without_group_filter(
    db: Session,
    collection_id: UUID,
) -> Optional[GroupRecitationCollection]:
    """Get a collection by ID only (for ownership validation)."""
    return (
        db.query(GroupRecitationCollection)
        .filter(
            GroupRecitationCollection.id == collection_id,
            GroupRecitationCollection.deleted_at.is_(None),
        )
        .first()
    )
