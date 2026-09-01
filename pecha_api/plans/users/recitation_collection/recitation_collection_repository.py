from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from typing import List, Optional, Tuple
from uuid import UUID
from fastapi import HTTPException
from starlette import status

from pecha_api.plans.users.recitation_collection.recitation_collection_models import (
    RecitationCollection,
    RecitationCollectionItem
)
from pecha_api.plans.auth.plan_auth_models import ResponseError
from pecha_api.plans.response_message import BAD_REQUEST


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


def get_all_user_collections(
    db: Session,
    user_id: UUID,
) -> List[RecitationCollection]:
    """Return all individual recitation collections for a user, newest first."""
    return (
        db.query(RecitationCollection)
        .filter(RecitationCollection.user_id == user_id)
        .order_by(RecitationCollection.created_at.desc())
        .all()
    )


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


def save_collection(
    db: Session,
    collection: RecitationCollection
) -> RecitationCollection:

    try:
        db.add(collection)
        db.commit()
        db.refresh(collection)
        return collection
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ResponseError(error=BAD_REQUEST, message=str(e.orig)).model_dump()
        )


def update_collection(
    db: Session,
    collection: RecitationCollection
) -> RecitationCollection:

    db.commit()
    db.refresh(collection)
    return collection


def get_max_display_order_for_collection(
    db: Session,
    collection_id: UUID
) -> Optional[int]:

    result = db.query(func.max(RecitationCollectionItem.display_order)).filter(
        RecitationCollectionItem.recitation_collection_id == collection_id
    ).scalar()
    return result


def save_collection_items(
    db: Session,
    items: List[RecitationCollectionItem]
) -> List[RecitationCollectionItem]:

    try:
        db.add_all(items)
        db.commit()
        for item in items:
            db.refresh(item)
        return items
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ResponseError(error=BAD_REQUEST, message=str(e.orig)).model_dump()
        )


def delete_collection(
    db: Session,
    collection_id: UUID,
    user_id: UUID
) -> Optional[RecitationCollection]:

    collection = get_collection_by_id(db=db, collection_id=collection_id, user_id=user_id)
    
    if not collection:
        return None
    
    try:
        db.delete(collection)
        db.commit()
        return collection
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ResponseError(error=BAD_REQUEST, message=str(e.orig)).model_dump()
        )
