from datetime import datetime, timedelta, timezone
import logging
from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from starlette import status

from pecha_api.db.database import SessionLocal
from pecha_api.plans.audio.audio_job_models import AudioJob
from pecha_api.plans.audio.audio_job_repository import (
    create_audio_job,
    get_audio_job_by_id,
    list_undispatched_pending_audio_jobs,
    mark_audio_job_completed,
    mark_audio_job_failed,
    mark_audio_job_processing,
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
from pecha_api.config import get, get_int

logger = logging.getLogger(__name__)


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


def _build_audio_job_message_body(job: AudioJob) -> dict:
    payload = job.payload if isinstance(job.payload, dict) else {}
    return {
        "job_id": str(job.id),
        "day_id": str(job.day_id) if job.day_id else payload.get("day_id"),
        "sub_task_id": str(job.sub_task_id) if job.sub_task_id else payload.get("sub_task_id"),
        "language": job.language or payload.get("language"),
        "type": job.audio_type or payload.get("type"),
        "voice_name": job.voice_name or payload.get("voice_name"),
    }


def _dispatch_audio_job_to_sqs(job: AudioJob) -> str:
    """Send the SQS message and persist MessageId. Raises HTTPException on send failure."""
    message_id = send_audio_job_message(_build_audio_job_message_body(job))
    with SessionLocal() as db:
        update_audio_job_sqs_message_id(db=db, job_id=job.id, sqs_message_id=message_id)
    return message_id


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

    # Persist first so workers always have a job_id. Undispatched rows
    # (crash between commit and SQS send) are marked failed by reconcile_undispatched_audio_jobs.
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

    try:
        _dispatch_audio_job_to_sqs(job)
    except HTTPException as e:
        with SessionLocal() as db:
            mark_audio_job_failed(
                db=db,
                job_id=job_id,
                error_message=str(e.detail),
            )
        raise

    return AudioJobAcceptedResponse(
        job_id=job_id,
        status=AudioJobStatus.PENDING,
    )


def reconcile_undispatched_audio_jobs() -> int:
    """Mark pending jobs that never recorded an SQS MessageId as failed.

    Covers the commit-before-send crash window. A grace period avoids racing
    an in-flight enqueue.
    """
    grace_seconds = max(get_int("AUDIO_JOB_DISPATCH_RECONCILE_GRACE_SECONDS"), 1)
    batch_size = max(get_int("AUDIO_JOB_DISPATCH_RECONCILE_BATCH_SIZE"), 1)
    older_than = datetime.now(timezone.utc) - timedelta(seconds=grace_seconds)
    error_message = "Audio job never dispatched to SQS"

    with SessionLocal() as db:
        jobs = list_undispatched_pending_audio_jobs(
            db=db,
            older_than=older_than,
            limit=batch_size,
        )
        job_ids = [job.id for job in jobs]

    marked_failed = 0
    for job_id in job_ids:
        with SessionLocal() as db:
            updated = mark_audio_job_failed(
                db=db,
                job_id=job_id,
                error_message=error_message,
                expected_statuses=(AudioJobStatus.PENDING.value,),
            )
        if updated:
            marked_failed += 1
            logger.info("Marked undispatched audio job %s as failed", job_id)

    return marked_failed


def _to_audio_job_status_response(job: AudioJob) -> AudioJobStatusResponse:
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


def get_audio_job_status(job_id: UUID) -> AudioJobStatusResponse:
    with SessionLocal() as db:
        job = get_audio_job_by_id(db=db, job_id=job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ResponseError(error=NOT_FOUND, message="Audio job not found").model_dump(),
            )
        return _to_audio_job_status_response(job)


def _job_not_found_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=ResponseError(error=NOT_FOUND, message="Audio job not found").model_dump(),
    )


def _job_conflict_error(message: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=ResponseError(error=BAD_REQUEST, message=message).model_dump(),
    )


def update_audio_job_status(
    *,
    job_id: UUID,
    next_status: AudioJobStatus,
    result: Optional[dict] = None,
    error_message: Optional[str] = None,
) -> AudioJobStatusResponse:
    terminal = {AudioJobStatus.COMPLETED.value, AudioJobStatus.FAILED.value}

    with SessionLocal() as db:
        if next_status == AudioJobStatus.PROCESSING:
            # Atomic PENDING -> PROCESSING claim so duplicate SQS deliveries
            # cannot both increment attempt_count or run generation.
            updated = mark_audio_job_processing(db=db, job_id=job_id)
            if updated:
                return _to_audio_job_status_response(updated)

            job = get_audio_job_by_id(db=db, job_id=job_id)
            if not job:
                raise _job_not_found_error()
            if job.status in terminal:
                return _to_audio_job_status_response(job)
            raise _job_conflict_error("Audio job is already being processed")

        if next_status == AudioJobStatus.COMPLETED:
            updated = mark_audio_job_completed(db=db, job_id=job_id, result=result or {})
            if updated:
                return _to_audio_job_status_response(updated)

            job = get_audio_job_by_id(db=db, job_id=job_id)
            if not job:
                raise _job_not_found_error()
            if job.status in terminal:
                return _to_audio_job_status_response(job)
            raise _job_conflict_error("Audio job cannot be completed from its current status")

        if next_status == AudioJobStatus.FAILED:
            updated = mark_audio_job_failed(
                db=db,
                job_id=job_id,
                error_message=error_message or "Audio job failed",
                expected_statuses=(AudioJobStatus.PROCESSING.value,),
            )
            if updated:
                return _to_audio_job_status_response(updated)

            job = get_audio_job_by_id(db=db, job_id=job_id)
            if not job:
                raise _job_not_found_error()
            if job.status in terminal:
                return _to_audio_job_status_response(job)
            raise _job_conflict_error("Audio job cannot be failed from its current status")

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ResponseError(
                error=BAD_REQUEST,
                message=f"Unsupported audio job status update: {next_status.value}",
            ).model_dump(),
        )
