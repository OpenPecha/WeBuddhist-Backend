import os
import uuid
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, UploadFile
from starlette import status

from pecha_api.config import get
from pecha_api.db.database import SessionLocal
from pecha_api.plans.audio.plan_day_audio_service import _validate_audio_file
from pecha_api.plans.auth.plan_auth_models import ResponseError
from pecha_api.plans.authors.plan_authors_service import validate_cms_author_details
from pecha_api.plans.cms.cms_plans_repository import get_plan_by_id
from pecha_api.plans.items.plan_items_repository import get_plan_item_by_id
from pecha_api.plans.media.media_response_models import SubTaskAudioUploadResponse
from pecha_api.plans.response_message import (
    BAD_REQUEST,
    PLAN_DAY_NOT_FOUND,
    PLAN_NOT_FOUND,
    SUB_TASK_NOT_FOUND,
    SUBTASK_AUDIO_UPLOAD_SUCCESS,
    TASK_NOT_FOUND,
)
from pecha_api.plans.shared.permissions import require_can_edit_content
from pecha_api.plans.tasks.plan_tasks_repository import get_task_by_id
from pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_models import PlanSubTask
from pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_repository import get_sub_task_by_subtask_id
from pecha_api.plans.public.plans_cache_service import schedule_invalidate_plan_day_cache_for_task
from pecha_api.uploads.S3_utils import delete_file, generate_presigned_access_url, upload_file


def _get_author_sub_task(db, sub_task_id: UUID, current_author) -> PlanSubTask:
    subtask = get_sub_task_by_subtask_id(db=db, id=sub_task_id)
    if not subtask:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ResponseError(error=BAD_REQUEST, message=SUB_TASK_NOT_FOUND).model_dump(),
        )

    task = get_task_by_id(db=db, task_id=subtask.task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ResponseError(error=BAD_REQUEST, message=TASK_NOT_FOUND).model_dump(),
        )

    plan_item = get_plan_item_by_id(db=db, day_id=task.plan_item_id)
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
    return subtask


def upload_plan_subtask_audio(
    token: str,
    sub_task_id: UUID,
    file: UploadFile,
    duration_ms: Optional[int] = None,
) -> SubTaskAudioUploadResponse:
    _validate_audio_file(file)
    file_extension = os.path.splitext(file.filename.lower())[1] if file.filename else ""

    with SessionLocal() as db:
        current_author = validate_cms_author_details(token=token)
        subtask = _get_author_sub_task(db=db, sub_task_id=sub_task_id, current_author=current_author)

        unique_id = str(uuid.uuid4())
        s3_key = f"audio/plan_subtasks/{subtask.task_id}/{sub_task_id}/{unique_id}{file_extension}"

        file.file.seek(0)
        upload_file(
            bucket_name=get("AWS_BUCKET_NAME"),
            s3_key=s3_key,
            file=file,
        )

        if subtask.audio_url:
            delete_file(subtask.audio_url)

        subtask.audio_url = s3_key
        subtask.duration = str(duration_ms) if duration_ms is not None else None
        subtask.updated_by = current_author.email
        db.commit()

        task_id_str = str(subtask.task_id)
        sub_task_id_str = str(sub_task_id)
        audio_key = s3_key
        stored_duration_ms = duration_ms
        schedule_invalidate_plan_day_cache_for_task(db=db, task_id=subtask.task_id)

    audio_url = generate_presigned_access_url(
        bucket_name=get("AWS_BUCKET_NAME"),
        s3_key=audio_key,
    )
    return SubTaskAudioUploadResponse(
        sub_task_id=sub_task_id_str,
        task_id=task_id_str,
        audio_key=audio_key,
        audio_url=audio_url,
        duration_ms=stored_duration_ms,
        message=SUBTASK_AUDIO_UPLOAD_SUCCESS,
    )


def delete_plan_subtask_audio(token: str, sub_task_id: UUID) -> None:
    with SessionLocal() as db:
        current_author = validate_cms_author_details(token=token)
        subtask = _get_author_sub_task(db=db, sub_task_id=sub_task_id, current_author=current_author)
        if subtask.audio_url:
            delete_file(subtask.audio_url)
        subtask.audio_url = None
        subtask.duration = None
        subtask.updated_by = current_author.email
        db.commit()
        schedule_invalidate_plan_day_cache_for_task(db=db, task_id=subtask.task_id)
