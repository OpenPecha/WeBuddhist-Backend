from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from starlette import status

from pecha_api.config import get
from pecha_api.db.database import SessionLocal
from pecha_api.plans.auth.plan_auth_models import ResponseError
from pecha_api.plans.authors.plan_authors_service import validate_cms_author_details
from pecha_api.plans.cms.cms_plans_repository import get_plan_by_id
from pecha_api.plans.items.plan_items_repository import get_plan_item_by_id
from pecha_api.plans.notifications.day_notification_models import DayNotification, ImageTypeEnum
from pecha_api.plans.notifications.day_notification_repository import (
    create_notification,
    delete_notification,
    get_notification_by_day_id,
    update_notification,
)
from pecha_api.plans.notifications.day_notification_response_models import (
    CreateNotificationRequest,
    NotificationDTO,
    UpdateNotificationRequest,
)
from pecha_api.plans.response_message import (
    BAD_REQUEST,
    NOTIFICATION_ALREADY_EXISTS,
    NOTIFICATION_CREATED,
    NOTIFICATION_NOT_FOUND,
    NOTIFICATION_UPDATED,
    PLAN_DAY_NOT_FOUND,
    PLAN_NOT_FOUND,
)
from pecha_api.plans.shared.permissions import require_can_edit_content
from pecha_api.uploads.S3_utils import generate_presigned_access_url


def _validate_author_and_get_plan_item(db, day_id: UUID, current_author):
    plan_item = get_plan_item_by_id(db=db, day_id=day_id)
    if not plan_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ResponseError(error=BAD_REQUEST, message=PLAN_DAY_NOT_FOUND).model_dump(),
        )
    
    plan = get_plan_by_id(db=db, plan_id=plan_item.plan_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ResponseError(error=BAD_REQUEST, message=PLAN_NOT_FOUND).model_dump(),
        )
    
    require_can_edit_content(
        db=db,
        group_id=plan.group_id,
        author=current_author,
        content_status=plan.status,
    )
    
    return plan_item


def _generate_notification_image_url(image_url: Optional[str]) -> Optional[str]:
    if not image_url:
        return None
    try:
        return generate_presigned_access_url(
            bucket_name=get("AWS_BUCKET_NAME"),
            s3_key=image_url,
        )
    except Exception:
        return None


def _notification_to_dto(notification: DayNotification) -> NotificationDTO:
    image_url = _generate_notification_image_url(notification.image_url)
    
    return NotificationDTO(
        id=notification.id,
        day_id=notification.day_id,
        title=notification.title,
        body=notification.body,
        image_type=notification.image_type.value if notification.image_type else None,
        image_url=image_url,
        created_at=notification.created_at,
        updated_at=notification.updated_at,
    )


def create_day_notification(
    token: str,
    day_id: UUID,
    request: CreateNotificationRequest,
) -> NotificationDTO:
    with SessionLocal() as db:
        current_author = validate_cms_author_details(token=token)
        plan_item = _validate_author_and_get_plan_item(db=db, day_id=day_id, current_author=current_author)
        
        existing = get_notification_by_day_id(db=db, day_id=day_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ResponseError(error=BAD_REQUEST, message=NOTIFICATION_ALREADY_EXISTS).model_dump(),
            )
        
        image_type_enum = None
        if request.image_type:
            try:
                image_type_enum = ImageTypeEnum(request.image_type.upper())
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=ResponseError(error=BAD_REQUEST, message="Invalid image_type. Must be 'PLAN' or 'CUSTOM'").model_dump(),
                )
        
        notification = DayNotification(
            day_id=day_id,
            title=request.title,
            body=request.body,
            image_type=image_type_enum,
            image_url=request.image_url,
        )
        
        created = create_notification(db=db, notification=notification)
    
    return _notification_to_dto(created)


def get_day_notification(token: str, day_id: UUID) -> NotificationDTO:
    with SessionLocal() as db:
        current_author = validate_cms_author_details(token=token)
        plan_item = _validate_author_and_get_plan_item(db=db, day_id=day_id, current_author=current_author)
        
        notification = get_notification_by_day_id(db=db, day_id=day_id)
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ResponseError(error=BAD_REQUEST, message=NOTIFICATION_NOT_FOUND).model_dump(),
            )
    
    return _notification_to_dto(notification)


def update_day_notification(
    token: str,
    day_id: UUID,
    request: UpdateNotificationRequest,
) -> NotificationDTO:
    with SessionLocal() as db:
        current_author = validate_cms_author_details(token=token)
        plan_item = _validate_author_and_get_plan_item(db=db, day_id=day_id, current_author=current_author)
        
        existing = get_notification_by_day_id(db=db, day_id=day_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ResponseError(error=BAD_REQUEST, message=NOTIFICATION_NOT_FOUND).model_dump(),
            )
        
        image_type_value = None
        if request.image_type is not None:
            try:
                image_type_enum = ImageTypeEnum(request.image_type.upper())
                image_type_value = image_type_enum
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=ResponseError(error=BAD_REQUEST, message="Invalid image_type. Must be 'PLAN' or 'CUSTOM'").model_dump(),
                )
        
        updated = update_notification(
            db=db,
            day_id=day_id,
            title=request.title,
            body=request.body,
            image_type=image_type_value,
            image_url=request.image_url,
        )
    
    return _notification_to_dto(updated)


def delete_day_notification(token: str, day_id: UUID) -> None:
    with SessionLocal() as db:
        current_author = validate_cms_author_details(token=token)
        plan_item = _validate_author_and_get_plan_item(db=db, day_id=day_id, current_author=current_author)
        
        existing = get_notification_by_day_id(db=db, day_id=day_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ResponseError(error=BAD_REQUEST, message=NOTIFICATION_NOT_FOUND).model_dump(),
            )
        
        delete_notification(db=db, day_id=day_id)
