from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from starlette import status

from pecha_api.db.database import SessionLocal
from pecha_api.notification.notification_models import Notification
from pecha_api.notification.notification_repository import (
    create_notification,
    get_notification_by_id,
    get_notifications_paginated,
    mark_notification_read,
)
from pecha_api.notification.notification_response_models import (
    NotificationDTO,
    NotificationListResponse,
)
from pecha_api.plans.authors.plan_authors_service import validate_and_extract_author_details


def _notification_to_dto(row: Notification) -> NotificationDTO:
    return NotificationDTO(
        id=row.id,
        title=row.title,
        description=row.description,
        category=row.category,
        reference_id=row.reference_id,
        is_read=bool(row.is_read),
        read_at=row.read_at,
        created_at=row.created_at,
    )


def create_notification_record(
    *,
    recipient_author_id: UUID,
    title: str,
    description: Optional[str],
    category: str,
    reference_id: Optional[UUID],
) -> Notification:
    notification = Notification(
        recipient_author_id=recipient_author_id,
        title=title,
        description=description,
        category=category,
        reference_id=reference_id,
    )
    with SessionLocal() as db:
        return create_notification(db=db, notification=notification)


def list_notifications(
    token: str,
    skip: int,
    limit: int,
    unread_only: bool = False,
) -> NotificationListResponse:
    author = validate_and_extract_author_details(token=token)
    with SessionLocal() as db:
        rows, total = get_notifications_paginated(
            db=db,
            recipient_author_id=author.id,
            skip=skip,
            limit=limit,
            unread_only=unread_only,
        )
    return NotificationListResponse(
        notifications=[_notification_to_dto(row) for row in rows],
        skip=skip,
        limit=limit,
        total=total,
    )


def mark_notification_as_read(token: str, notification_id: UUID) -> NotificationDTO:
    author = validate_and_extract_author_details(token=token)
    with SessionLocal() as db:
        row = get_notification_by_id(
            db=db,
            notification_id=notification_id,
            recipient_author_id=author.id,
        )
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found",
            )
        updated = mark_notification_read(db=db, notification=row)
    return _notification_to_dto(updated)
