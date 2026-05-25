import mimetypes
import os
import uuid
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, UploadFile
from starlette import status

from pecha_api.config import DEFAULTS, get, get_int
from pecha_api.db.database import SessionLocal
from pecha_api.plans.audio.plan_item_audio_models import PlanItemAudio
from pecha_api.plans.audio.plan_item_audio_repository import (
    delete_plan_item_audio,
    get_plan_item_audio_by_plan_item_id,
    upsert_plan_item_audio,
)
from pecha_api.plans.auth.plan_auth_models import ResponseError
from pecha_api.plans.authors.plan_authors_service import validate_and_extract_author_details
from pecha_api.plans.cms.cms_plans_repository import get_plan_by_id
from pecha_api.plans.items.plan_items_repository import get_plan_item
from pecha_api.plans.media.media_response_models import PlanDayAudioUploadResponse
from pecha_api.plans.response_message import (
    AUDIO_FILE_TOO_LARGE,
    AUDIO_UPLOAD_SUCCESS,
    BAD_REQUEST,
    INVALID_AUDIO_FILE_FORMAT,
    PLAN_NOT_FOUND,
)
from pecha_api.uploads.S3_utils import delete_file, generate_presigned_access_url, upload_file


def _validate_audio_file(file: UploadFile) -> None:
    file_extension = os.path.splitext(file.filename.lower())[1] if file.filename else ""
    allowed_extensions = DEFAULTS["ALLOWED_AUDIO_EXTENSIONS"]
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=INVALID_AUDIO_FILE_FORMAT,
        )
    if hasattr(file, "size") and file.size and file.size > get_int("MAX_AUDIO_FILE_SIZE"):
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=AUDIO_FILE_TOO_LARGE,
        )


def _get_author_plan_item(db, plan_id: UUID, day_id: UUID, token: str):
    current_author = validate_and_extract_author_details(token=token)
    plan = get_plan_by_id(db=db, plan_id=plan_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ResponseError(error=BAD_REQUEST, message=PLAN_NOT_FOUND).model_dump(),
        )
    if not current_author.is_admin and plan.author_id != current_author.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ResponseError(error=BAD_REQUEST, message=PLAN_NOT_FOUND).model_dump(),
        )
    return get_plan_item(db=db, plan_id=plan_id, day_id=day_id)


def upload_plan_day_audio(
    token: str,
    plan_id: UUID,
    day_id: UUID,
    file: UploadFile,
    duration_ms: Optional[int] = None,
) -> PlanDayAudioUploadResponse:
    _validate_audio_file(file)
    file_extension = os.path.splitext(file.filename.lower())[1] if file.filename else ""
    content_type = file.content_type or mimetypes.guess_type(file.filename or "")[0] or "audio/mpeg"

    with SessionLocal() as db:
        current_author = validate_and_extract_author_details(token=token)
        plan_item = _get_author_plan_item(db=db, plan_id=plan_id, day_id=day_id, token=token)

        unique_id = str(uuid.uuid4())
        s3_key = f"audio/plan_days/{plan_id}/{day_id}/{unique_id}{file_extension}"

        file.file.seek(0)
        upload_file(
            bucket_name=get("AWS_BUCKET_NAME"),
            s3_key=s3_key,
            file=file,
        )

        existing = get_plan_item_audio_by_plan_item_id(db=db, plan_item_id=plan_item.id)
        if existing and existing.audio_key:
            delete_file(existing.audio_key)

        file_size = file.size if hasattr(file, "size") and file.size else None
        audio_row = upsert_plan_item_audio(
            db=db,
            plan_item_audio=PlanItemAudio(
                plan_item_id=plan_item.id,
                audio_key=s3_key,
                duration_ms=duration_ms,
                mime_type=content_type,
                file_size_bytes=file_size,
                created_by=current_author.email,
            ),
        )

    audio_url = generate_presigned_access_url(
        bucket_name=get("AWS_BUCKET_NAME"),
        s3_key=audio_row.audio_key,
    )
    return PlanDayAudioUploadResponse(
        plan_item_id=str(plan_item.id),
        audio_key=audio_row.audio_key,
        audio_url=audio_url,
        duration_ms=audio_row.duration_ms,
        message=AUDIO_UPLOAD_SUCCESS,
    )


def delete_plan_day_audio(token: str, plan_id: UUID, day_id: UUID) -> None:
    with SessionLocal() as db:
        plan_item = _get_author_plan_item(db=db, plan_id=plan_id, day_id=day_id, token=token)
        existing = get_plan_item_audio_by_plan_item_id(db=db, plan_item_id=plan_item.id)
        if existing and existing.audio_key:
            delete_file(existing.audio_key)
        delete_plan_item_audio(db=db, plan_item_id=plan_item.id)
