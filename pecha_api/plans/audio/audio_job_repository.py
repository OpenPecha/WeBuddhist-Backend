from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence
from uuid import UUID

from sqlalchemy import update
from sqlalchemy.orm import Session

from pecha_api.plans.audio.audio_job_models import AudioJob
from pecha_api.plans.plans_enums import AudioJobStatus


def create_audio_job(db: Session, audio_job: AudioJob) -> AudioJob:
    db.add(audio_job)
    db.commit()
    db.refresh(audio_job)
    return audio_job


def get_audio_job_by_id(db: Session, job_id: UUID) -> Optional[AudioJob]:
    return db.query(AudioJob).filter(AudioJob.id == job_id).first()


def list_undispatched_pending_audio_jobs(
    db: Session,
    *,
    older_than: datetime,
    limit: int = 50,
) -> List[AudioJob]:
    """Pending jobs never recorded as dispatched to SQS (commit-before-send crash)."""
    return (
        db.query(AudioJob)
        .filter(
            AudioJob.status == AudioJobStatus.PENDING.value,
            AudioJob.sqs_message_id.is_(None),
            AudioJob.created_at <= older_than,
        )
        .order_by(AudioJob.created_at.asc())
        .limit(limit)
        .all()
    )


def update_audio_job_sqs_message_id(
    db: Session,
    job_id: UUID,
    sqs_message_id: str,
) -> Optional[AudioJob]:
    job = get_audio_job_by_id(db=db, job_id=job_id)
    if not job:
        return None
    job.sqs_message_id = sqs_message_id
    db.commit()
    db.refresh(job)
    return job


def mark_audio_job_processing(db: Session, job_id: UUID) -> Optional[AudioJob]:
    """Atomically claim a pending job for processing.

    Only one concurrent caller can win the PENDING -> PROCESSING transition.
    Returns None when the job is missing or was already claimed/finished.
    """
    now = datetime.now(timezone.utc)
    result = db.execute(
        update(AudioJob)
        .where(
            AudioJob.id == job_id,
            AudioJob.status == AudioJobStatus.PENDING.value,
        )
        .values(
            status=AudioJobStatus.PROCESSING.value,
            started_at=now,
            attempt_count=AudioJob.attempt_count + 1,
            error_message=None,
            updated_at=now,
        )
    )
    db.commit()
    if result.rowcount == 0:
        return None
    return get_audio_job_by_id(db=db, job_id=job_id)


def mark_audio_job_completed(
    db: Session,
    job_id: UUID,
    result: Dict[str, Any],
) -> Optional[AudioJob]:
    """Atomically complete a processing job. Returns None if not in PROCESSING."""
    now = datetime.now(timezone.utc)
    update_result = db.execute(
        update(AudioJob)
        .where(
            AudioJob.id == job_id,
            AudioJob.status == AudioJobStatus.PROCESSING.value,
        )
        .values(
            status=AudioJobStatus.COMPLETED.value,
            result=result,
            error_message=None,
            completed_at=now,
            updated_at=now,
        )
    )
    db.commit()
    if update_result.rowcount == 0:
        return None
    return get_audio_job_by_id(db=db, job_id=job_id)


def mark_audio_job_failed(
    db: Session,
    job_id: UUID,
    error_message: str,
    *,
    expected_statuses: Optional[Sequence[str]] = None,
) -> Optional[AudioJob]:
    """Atomically fail a job from an allowed status set.

    Defaults to PENDING or PROCESSING so enqueue failures and worker failures
    both work. Pass expected_statuses to restrict (e.g. PROCESSING only).
    """
    statuses = list(expected_statuses) if expected_statuses is not None else [
        AudioJobStatus.PENDING.value,
        AudioJobStatus.PROCESSING.value,
    ]
    now = datetime.now(timezone.utc)
    update_result = db.execute(
        update(AudioJob)
        .where(
            AudioJob.id == job_id,
            AudioJob.status.in_(statuses),
        )
        .values(
            status=AudioJobStatus.FAILED.value,
            error_message=error_message,
            completed_at=now,
            updated_at=now,
        )
    )
    db.commit()
    if update_result.rowcount == 0:
        return None
    return get_audio_job_by_id(db=db, job_id=job_id)
