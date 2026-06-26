import os
import uuid
from uuid import UUID

from fastapi import HTTPException, UploadFile
from starlette import status

from pecha_api.config import get
from pecha_api.db.database import SessionLocal
from pecha_api.image_utils import WEBP_CONTENT_TYPE, WEBP_EXTENSION, ImageUtils
from pecha_api.plans.auth.plan_auth_models import ResponseError
from pecha_api.plans.authors.plan_authors_service import validate_cms_author_details
from pecha_api.plans.cms.cms_plans_repository import get_plan_by_id
from pecha_api.plans.items.plan_items_repository import get_plan_item_by_id
from pecha_api.plans.response_message import (
    BAD_REQUEST,
    PLAN_DAY_NOT_FOUND,
    PLAN_NOT_FOUND,
)
from pecha_api.plans.shareable_images.day_shareable_image_enums import DayShareableImageType
from pecha_api.plans.shareable_images.day_shareable_image_models import DayShareableImage
from pecha_api.plans.shareable_images.day_shareable_image_repository import (
    clear_day_shareable_image_key,
    get_day_shareable_image_by_plan_item_id,
    upsert_day_shareable_image,
)
from pecha_api.plans.shareable_images.day_shareable_image_response_models import (
    PlanDayShareableImageUploadResponse,
)
from pecha_api.plans.shared.permissions import require_can_edit_content
from pecha_api.uploads.S3_utils import delete_file, generate_presigned_access_url, upload_bytes


def _get_author_plan_item_by_day_id(db, day_id: UUID, current_author):
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


def upload_plan_day_shareable_image(
    token: str,
    day_id: UUID,
    image_type: DayShareableImageType,
    file: UploadFile,
) -> PlanDayShareableImageUploadResponse:
    image_utils = ImageUtils()
    compressed_image = image_utils.validate_and_compress_image(
        file=file,
        content_type=file.content_type or "image/jpeg",
    )
    file_name, _ = os.path.splitext(file.filename or "image")
    unique_id = str(uuid.uuid4())

    with SessionLocal() as db:
        current_author = validate_cms_author_details(token=token)
        plan_item = _get_author_plan_item_by_day_id(
            db=db, day_id=day_id, current_author=current_author
        )

        s3_key = (
            f"images/day_shareable/{plan_item.plan_id}/{day_id}/"
            f"{image_type.value}/{unique_id}/{file_name}{WEBP_EXTENSION}"
        )

        upload_bytes(
            bucket_name=get("AWS_BUCKET_NAME"),
            s3_key=s3_key,
            file=compressed_image,
            content_type=WEBP_CONTENT_TYPE,
        )

        existing = get_day_shareable_image_by_plan_item_id(
            db=db, plan_item_id=plan_item.id
        )
        old_key = None
        if existing:
            if image_type == DayShareableImageType.THUMBNAIL:
                old_key = existing.thumbnail_key
            else:
                old_key = existing.shareable_image_key

        if old_key:
            delete_file(old_key)

        row_kwargs = {
            "plan_item_id": plan_item.id,
            "created_by": current_author.email,
            "updated_by": current_author.email,
        }
        if image_type == DayShareableImageType.THUMBNAIL:
            row_kwargs["thumbnail_key"] = s3_key
        else:
            row_kwargs["shareable_image_key"] = s3_key

        image_row = upsert_day_shareable_image(
            db=db,
            day_shareable_image=DayShareableImage(**row_kwargs),
        )

        plan_item_id_str = str(plan_item.id)
        if image_type == DayShareableImageType.THUMBNAIL:
            image_key = image_row.thumbnail_key
        else:
            image_key = image_row.shareable_image_key

    image_url = generate_presigned_access_url(
        bucket_name=get("AWS_BUCKET_NAME"),
        s3_key=image_key,
    )
    return PlanDayShareableImageUploadResponse(
        plan_item_id=plan_item_id_str,
        image_type=image_type.value,
        image_key=image_key,
        image_url=image_url,
    )


def delete_plan_day_shareable_image(
    token: str,
    day_id: UUID,
    image_type: DayShareableImageType,
) -> None:
    with SessionLocal() as db:
        current_author = validate_cms_author_details(token=token)
        plan_item = _get_author_plan_item_by_day_id(
            db=db, day_id=day_id, current_author=current_author
        )
        existing = get_day_shareable_image_by_plan_item_id(
            db=db, plan_item_id=plan_item.id
        )
        if not existing:
            return

        old_key = (
            existing.thumbnail_key
            if image_type == DayShareableImageType.THUMBNAIL
            else existing.shareable_image_key
        )
        if old_key:
            delete_file(old_key)

        clear_day_shareable_image_key(
            db=db,
            plan_item_id=plan_item.id,
            thumbnail_key=image_type == DayShareableImageType.THUMBNAIL,
            shareable_image_key=image_type == DayShareableImageType.SHAREABLE_IMAGE,
            updated_by=current_author.email,
        )
