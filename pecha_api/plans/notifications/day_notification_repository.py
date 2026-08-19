from typing import Optional, Union
from uuid import UUID

from sqlalchemy.orm import Session

from pecha_api.plans.notifications.day_notification_models import DayNotification, ImageTypeEnum


def get_notification_by_day_id(db: Session, day_id: UUID) -> Optional[DayNotification]:
    return (
        db.query(DayNotification)
        .filter(DayNotification.day_id == day_id)
        .first()
    )


def create_notification(db: Session, notification: DayNotification) -> DayNotification:
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def update_notification(
    db: Session,
    day_id: UUID,
    title: Optional[str] = None,
    body: Optional[str] = None,
    image_type: Optional[ImageTypeEnum] = None,
    image_url: Optional[str] = None,
) -> Optional[DayNotification]:
    notification = get_notification_by_day_id(db=db, day_id=day_id)
    if not notification:
        return None
    
    if title is not None:
        notification.title = title
    if body is not None:
        notification.body = body
    if image_type is not None:
        notification.image_type = image_type
    if image_url is not None:
        notification.image_url = image_url
    
    from _datetime import datetime
    import _datetime
    notification.updated_at = datetime.now(_datetime.timezone.utc)
    
    db.commit()
    db.refresh(notification)
    return notification


def delete_notification(db: Session, day_id: UUID) -> None:
    db.query(DayNotification).filter(DayNotification.day_id == day_id).delete()
    db.commit()
