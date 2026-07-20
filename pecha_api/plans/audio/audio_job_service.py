from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from starlette import status

from pecha_api.db.database import SessionLocal
from pecha_api.plans.audio.audio_job_models import AudioJob
from pecha_api.plans.audio.audio_job_repository import (
    create_audio_job,
    get_audio_job_by_id,
    mark_audio_job_failed,
    update_audio_job_sqs_message_id,
)
from pecha_api.plans.audio.plan_audio_response_models import (
    AudioJobAcceptedResponse,
    AudioJobStatusResponse,
)
from pecha_api.plans.audio.sqs_client import send_audio_job_message
from pecha_api.plans.auth.plan_auth_models import ResponseError
from pecha_api.plans.items.plan_items_repository import get_plan_day_by_id_any_plan
from pecha_api.plans.plans_enums import (
    AudioJobStatus,
    ContentType,
    MonlamVoiceName,
    PlanAudioType,
)
from pecha_api.plans.response_message import BAD_REQUEST, NOT_FOUND
from pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_repository import get_sub_task_by_subtask_id
from pecha_api.uploads.S3_utils import generate_presigned_access_url
from pecha_api.config import get


def _audio_type_value(audio_type: PlanAudioType) -> str:
    return audio_type.value if hasattr(audio_type, "value") else str(audio_type)


def _voice_name_value(voice_name: MonlamVoiceName) -> str:
    return voice_name.value if hasattr(voice_name, "value") else str(voice_name)


def _validate_audio_job_target(
    *,
    day_id: Optional[UUID],
    sub_task_id: Optional[UUID],
) -> None:
    with SessionLocal() as db:
        if sub_task_id:
            subtask = get_sub_task_by_subtask_id(db=db, id=sub_task_id)
            if not subtask:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=ResponseError(error=BAD_REQUEST, message="Sub task not found").model_dump(),
                )
            allowed_types = {ContentType.TEXT, ContentType.SOURCE_REFERENCE}
            if subtask.content_type not in allowed_types:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=ResponseError(
                        error=BAD_REQUEST,
                        message="Sub task content type must be TEXT or SOURCE_REFERENCE for audio generation",
                    ).model_dump(),
                )
            return

        get_plan_day_by_id_any_plan(db=db, day_id=day_id)


def enqueue_plan_audio_job(
    *,
    language: str,
    day_id: Optional[UUID] = None,
    sub_task_id: Optional[UUID] = None,
    audio_type: PlanAudioType = PlanAudioType.TEXT_READING,
    voice_name: MonlamVoiceName = MonlamVoiceName.DOLKAR_LHASA_FEMALE,
    created_by: Optional[str] = None,
) -> AudioJobAcceptedResponse:
    _validate_audio_job_target(day_id=day_id, sub_task_id=sub_task_id)

    audio_type_value = _audio_type_value(audio_type)
    voice_name_value = _voice_name_value(voice_name)
    payload = {
        "day_id": str(day_id) if day_id else None,
        "sub_task_id": str(sub_task_id) if sub_task_id else None,
        "language": language,
        "type": audio_type_value,
        "voice_name": voice_name_value,
    }

    with SessionLocal() as db:
        job = create_audio_job(
            db=db,
            audio_job=AudioJob(
                status=AudioJobStatus.PENDING.value,
                day_id=day_id,
                sub_task_id=sub_task_id,
                language=language,
                audio_type=audio_type_value,
                voice_name=voice_name_value,
                payload=payload,
                created_by=created_by,
            ),
        )
        job_id = job.id

    message_body = {
        "job_id": str(job_id),
        **payload,
    }

    try:
        message_id = send_audio_job_message(message_body)
    except HTTPException as e:
        with SessionLocal() as db:
            mark_audio_job_failed(
                db=db,
                job_id=job_id,
                error_message=str(e.detail),
            )
        raise

    with SessionLocal() as db:
        update_audio_job_sqs_message_id(db=db, job_id=job_id, sqs_message_id=message_id)

    return AudioJobAcceptedResponse(
        job_id=job_id,
        status=AudioJobStatus.PENDING,
    )


def get_audio_job_status(job_id: UUID) -> AudioJobStatusResponse:
    with SessionLocal() as db:
        job = get_audio_job_by_id(db=db, job_id=job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ResponseError(error=NOT_FOUND, message="Audio job not found").model_dump(),
            )

        result = job.result or {}
        audio_url = result.get("audio_url")
        s3_key = result.get("s3_key")
        if s3_key and not audio_url:
            audio_url = generate_presigned_access_url(
                bucket_name=get("AWS_BUCKET_NAME"),
                s3_key=s3_key,
            )

        try:
            status_value = AudioJobStatus(job.status)
        except ValueError:
            status_value = AudioJobStatus.FAILED

        return AudioJobStatusResponse(
            job_id=job.id,
            status=status_value,
            day_id=job.day_id,
            sub_task_id=job.sub_task_id,
            language=job.language,
            type=job.audio_type,
            voice_name=job.voice_name,
            audio_url=audio_url,
            audio_duration_ms=result.get("audio_duration_ms"),
            s3_key=s3_key,
            error_message=job.error_message,
            created_at=job.created_at,
            updated_at=job.updated_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
        )
