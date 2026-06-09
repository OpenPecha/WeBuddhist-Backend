from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Tuple
from uuid import UUID

from pecha_api.plans.users.recitation_collection.recitation_collection_models import (
    RecitationCollection,
    RecitationCollectionItem
)


def get_user_collections(
    db: Session,
    user_id: UUID,
    skip: int = 0,
    limit: int = 20
) -> Tuple[List[RecitationCollection], int]:

    query = db.query(RecitationCollection).filter(
        RecitationCollection.user_id == user_id
    ).order_by(RecitationCollection.created_at.desc())
    
    total = query.count()
    collections = query.offset(skip).limit(limit).all()
    
    return collections, total


def get_collection_item_counts(
    db: Session,
    collection_ids: List[UUID]
) -> dict:

    if not collection_ids:
        return {}
    
    counts = db.query(
        RecitationCollectionItem.recitation_collection_id,
        func.count(RecitationCollectionItem.id).label('count')
    ).filter(
        RecitationCollectionItem.recitation_collection_id.in_(collection_ids)
    ).group_by(
        RecitationCollectionItem.recitation_collection_id
    ).all()
    
    return {row[0]: row[1] for row in counts}


def get_collection_by_id(
    db: Session,
    collection_id: UUID,
    user_id: UUID
) -> Optional[RecitationCollection]:

    return db.query(RecitationCollection).filter(
        RecitationCollection.id == collection_id,
        RecitationCollection.user_id == user_id
    ).first()


def get_collection_items(
    db: Session,
    collection_id: UUID
) -> List[RecitationCollectionItem]:

    return db.query(RecitationCollectionItem).filter(
        RecitationCollectionItem.recitation_collection_id == collection_id
    ).order_by(RecitationCollectionItem.display_order).all()
