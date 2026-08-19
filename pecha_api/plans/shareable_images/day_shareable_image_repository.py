from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from pecha_api.plans.shareable_images.day_shareable_image_models import DayShareableImage


def get_day_shareable_image_by_plan_item_id(
    db: Session, plan_item_id: UUID
) -> Optional[DayShareableImage]:
    return (
        db.query(DayShareableImage)
        .filter(DayShareableImage.plan_item_id == plan_item_id)
        .first()
    )


def get_day_shareable_images_by_plan_item_ids(
    db: Session, plan_item_ids: List[UUID]
) -> List[DayShareableImage]:
    if not plan_item_ids:
        return []
    return (
        db.query(DayShareableImage)
        .filter(DayShareableImage.plan_item_id.in_(plan_item_ids))
        .all()
    )


def upsert_day_shareable_image(
    db: Session, day_shareable_image: DayShareableImage
) -> DayShareableImage:
    existing = get_day_shareable_image_by_plan_item_id(
        db=db, plan_item_id=day_shareable_image.plan_item_id
    )
    if existing:
        if day_shareable_image.thumbnail_key is not None:
            existing.thumbnail_key = day_shareable_image.thumbnail_key
        if day_shareable_image.shareable_image_key is not None:
            existing.shareable_image_key = day_shareable_image.shareable_image_key
        existing.updated_by = day_shareable_image.updated_by
        db.commit()
        db.refresh(existing)
        return existing
    db.add(day_shareable_image)
    db.commit()
    db.refresh(day_shareable_image)
    return day_shareable_image


def clear_day_shareable_image_key(
    db: Session,
    plan_item_id: UUID,
    *,
    thumbnail_key: bool = False,
    shareable_image_key: bool = False,
    updated_by: Optional[str] = None,
) -> Optional[DayShareableImage]:
    existing = get_day_shareable_image_by_plan_item_id(db=db, plan_item_id=plan_item_id)
    if not existing:
        return None
    if thumbnail_key:
        existing.thumbnail_key = None
    if shareable_image_key:
        existing.shareable_image_key = None
    existing.updated_by = updated_by
    if not existing.thumbnail_key and not existing.shareable_image_key:
        db.delete(existing)
        db.commit()
        return None
    db.commit()
    db.refresh(existing)
    return existing
