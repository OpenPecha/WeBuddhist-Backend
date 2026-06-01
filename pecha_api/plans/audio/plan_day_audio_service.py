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
    count_plan_item_audio_by_audio_key,
    delete_plan_item_audio,
    get_accessible_plan_item_audio_by_key,
    get_plan_item_audio_by_plan_item_id,
    upsert_plan_item_audio,
)
from pecha_api.plans.audio.plan_audio_response_models import AssignPlanDayAudioRequest
from pecha_api.plans.auth.plan_auth_models import ResponseError
from pecha_api.plans.authors.plan_authors_service import validate_and_extract_author_details
from pecha_api.plans.cms.cms_plans_repository import get_plan_by_id
from pecha_api.plans.items.plan_items_repository import get_plan_item_by_id
from pecha_api.plans.media.media_response_models import PlanDayAudioUploadResponse
from pecha_api.plans.response_message import (
    AUDIO_ASSIGN_SUCCESS,
    AUDIO_FILE_TOO_LARGE,
    AUDIO_KEY_NOT_FOUND,
    AUDIO_UPLOAD_SUCCESS,
    BAD_REQUEST,
    INVALID_AUDIO_FILE_FORMAT,
    PLAN_DAY_NOT_FOUND,
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


def _get_author_plan_item_by_day_id(db, day_id: UUID, token: str):
    current_author = validate_and_extract_author_details(token=token)
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
    if not current_author.is_admin and plan.author_id != current_author.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ResponseError(error=BAD_REQUEST, message=PLAN_NOT_FOUND).model_dump(),
        )
    return plan_item


def upload_plan_day_audio(
    token: str,
    day_id: UUID,
    file: UploadFile,
    duration_ms: Optional[int] = None,
) -> PlanDayAudioUploadResponse:
    _validate_audio_file(file)
    file_extension = os.path.splitext(file.filename.lower())[1] if file.filename else ""
    content_type = file.content_type or mimetypes.guess_type(file.filename or "")[0] or "audio/mpeg"

    with SessionLocal() as db:
        current_author = validate_and_extract_author_details(token=token)
        plan_item = _get_author_plan_item_by_day_id(db=db, day_id=day_id, token=token)

        unique_id = str(uuid.uuid4())
        s3_key = f"audio/plan_days/{plan_item.plan_id}/{day_id}/{unique_id}{file_extension}"

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

        plan_item_id_str = str(plan_item.id)
        audio_key = audio_row.audio_key
        audio_duration_ms = audio_row.duration_ms

    audio_url = generate_presigned_access_url(
        bucket_name=get("AWS_BUCKET_NAME"),
        s3_key=audio_key,
    )
    return PlanDayAudioUploadResponse(
        plan_item_id=plan_item_id_str,
        audio_key=audio_key,
        audio_url=audio_url,
        duration_ms=audio_duration_ms,
        message=AUDIO_UPLOAD_SUCCESS,
    )


def assign_plan_day_audio(
    token: str,
    day_id: UUID,
    request: AssignPlanDayAudioRequest,
) -> PlanDayAudioUploadResponse:
    audio_key = request.audio_key.strip()
    if not audio_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ResponseError(error=BAD_REQUEST, message=AUDIO_KEY_NOT_FOUND).model_dump(),
        )

    with SessionLocal() as db:
        current_author = validate_and_extract_author_details(token=token)
        plan_item = _get_author_plan_item_by_day_id(db=db, day_id=day_id, token=token)

        source_audio = get_accessible_plan_item_audio_by_key(
            db=db,
            audio_key=audio_key,
            author_id=current_author.id,
            is_admin=current_author.is_admin,
        )
        if not source_audio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ResponseError(error=BAD_REQUEST, message=AUDIO_KEY_NOT_FOUND).model_dump(),
            )

        existing = get_plan_item_audio_by_plan_item_id(db=db, plan_item_id=plan_item.id)
        old_key = existing.audio_key if existing else None
        if old_key and old_key != audio_key and count_plan_item_audio_by_audio_key(db, old_key) <= 1:
            delete_file(old_key)

        duration_ms = (
            request.duration_ms
            if request.duration_ms is not None
            else source_audio.duration_ms
        )
        audio_row = upsert_plan_item_audio(
            db=db,
            plan_item_audio=PlanItemAudio(
                plan_item_id=plan_item.id,
                audio_key=audio_key,
                duration_ms=duration_ms,
                mime_type=source_audio.mime_type,
                file_size_bytes=source_audio.file_size_bytes,
                created_by=current_author.email,
                updated_by=current_author.email,
            ),
        )

        plan_item_id_str = str(plan_item.id)
        assigned_key = audio_row.audio_key
        assigned_duration_ms = audio_row.duration_ms

    audio_url = generate_presigned_access_url(
        bucket_name=get("AWS_BUCKET_NAME"),
        s3_key=assigned_key,
    )
    return PlanDayAudioUploadResponse(
        plan_item_id=plan_item_id_str,
        audio_key=assigned_key,
        audio_url=audio_url,
        duration_ms=assigned_duration_ms,
        message=AUDIO_ASSIGN_SUCCESS,
    )


def delete_plan_day_audio(token: str, day_id: UUID) -> None:
    with SessionLocal() as db:
        plan_item = _get_author_plan_item_by_day_id(db=db, day_id=day_id, token=token)
        existing = get_plan_item_audio_by_plan_item_id(db=db, plan_item_id=plan_item.id)
        if existing and existing.audio_key:
            delete_file(existing.audio_key)
        delete_plan_item_audio(db=db, plan_item_id=plan_item.id)
