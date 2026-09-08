from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from pecha_api.region_restrictions.region_restriction_enums import RestrictedItemType
from pecha_api.region_restrictions.region_restriction_models import ChinaRestrictedItem


def get_all_china_restricted_items(db: Session) -> List[ChinaRestrictedItem]:
    return db.query(ChinaRestrictedItem).all()


def list_china_restricted_items(
    db: Session,
    *,
    skip: int,
    limit: int,
    item_type: Optional[RestrictedItemType] = None,
) -> Tuple[List[ChinaRestrictedItem], int]:
    query = db.query(ChinaRestrictedItem)
    if item_type is not None:
        query = query.filter(ChinaRestrictedItem.item_type == item_type)
    total = query.count()
    rows = (
        query.order_by(ChinaRestrictedItem.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return rows, total


def create_china_restricted_item(
    db: Session,
    *,
    item_type: RestrictedItemType,
    item_id: str,
) -> ChinaRestrictedItem:
    row = ChinaRestrictedItem(item_type=item_type, item_id=item_id)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def delete_china_restricted_item_by_id(db: Session, *, row_id: UUID) -> bool:
    row = db.query(ChinaRestrictedItem).filter(ChinaRestrictedItem.id == row_id).first()
    if row is None:
        return False
    db.delete(row)
    db.commit()
    return True


def is_item_restricted_in_china(
    db: Session,
    *,
    item_type: RestrictedItemType,
    item_id: str,
) -> bool:
    return (
        db.query(ChinaRestrictedItem.id)
        .filter(
            ChinaRestrictedItem.item_type == item_type,
            ChinaRestrictedItem.item_id == item_id,
        )
        .first()
        is not None
    )
