from datetime import datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from pecha_api.notification.notification_models import Notification


def create_notification(db: Session, notification: Notification) -> Notification:
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def get_notification_by_id(
    db: Session,
    notification_id: UUID,
    recipient_author_id: Optional[UUID] = None,
) -> Optional[Notification]:
    query = db.query(Notification).filter(Notification.id == notification_id)
    if recipient_author_id is not None:
        query = query.filter(Notification.recipient_author_id == recipient_author_id)
    return query.first()


def get_notifications_paginated(
    db: Session,
    recipient_author_id: UUID,
    skip: int,
    limit: int,
    unread_only: bool = False,
) -> Tuple[List[Notification], int]:
    query = db.query(Notification).filter(
        Notification.recipient_author_id == recipient_author_id
    )
    if unread_only:
        query = query.filter(Notification.is_read.is_(False))
    total = query.count()
    rows = (
        query.order_by(Notification.created_at.desc(), Notification.id.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return rows, total


def mark_notification_read(db: Session, notification: Notification) -> Notification:
    if notification.is_read:
        return notification
    notification.is_read = True
    notification.read_at = datetime.now(timezone.utc)
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification


def mark_notifications_read_by_reference(
    db: Session,
    *,
    recipient_author_id: UUID,
    category: str,
    reference_id: UUID,
) -> None:
    rows = (
        db.query(Notification)
        .filter(
            Notification.recipient_author_id == recipient_author_id,
            Notification.category == category,
            Notification.reference_id == reference_id,
            Notification.is_read.is_(False),
        )
        .all()
    )
    if not rows:
        return
    now = datetime.now(timezone.utc)
    for row in rows:
        row.is_read = True
        row.read_at = now
        db.add(row)
    db.commit()
