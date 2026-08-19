from typing import Optional, Tuple
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session
from starlette import status

from pecha_api.db.database import SessionLocal
from pecha_api.plans.audio.plan_item_audio_repository import get_plan_item_audio_by_plan_item_id
from pecha_api.plans.audio.plan_subtask_audio_service import _get_author_sub_task
from pecha_api.plans.audio.sub_task_timestamps_repository import (
    delete_sub_task_timestamp,
    upsert_sub_task_timestamp,
)
from pecha_api.plans.authors.plan_authors_service import validate_cms_author_details
from pecha_api.plans.auth.plan_auth_models import ResponseError
from pecha_api.plans.response_message import BAD_REQUEST
from pecha_api.plans.tasks.plan_tasks_models import PlanTask
from pecha_api.plans.tasks.plan_tasks_repository import get_task_by_id


def validate_timestamp_pair(start_ms: Optional[int], end_ms: Optional[int]) -> None:
    has_start = start_ms is not None
    has_end = end_ms is not None
    if has_start != has_end:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ResponseError(
                error=BAD_REQUEST,
                message="start_ms and end_ms must both be provided or both omitted",
            ).model_dump(),
        )


def validate_timestamp_range(start_ms: int, end_ms: int, duration_ms: Optional[int]) -> None:
    if end_ms <= start_ms:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ResponseError(
                error=BAD_REQUEST,
                message="end_ms must be greater than start_ms",
            ).model_dump(),
        )
    if duration_ms is not None and end_ms > duration_ms:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ResponseError(
                error=BAD_REQUEST,
                message="end_ms must not exceed day audio duration_ms",
            ).model_dump(),
        )


def get_day_audio_duration_ms(db: Session, task_id: UUID) -> Optional[int]:
    task = get_task_by_id(db=db, task_id=task_id)
    if not task:
        return None
    audio = get_plan_item_audio_by_plan_item_id(db=db, plan_item_id=task.plan_item_id)
    if not audio:
        return None
    return audio.duration_ms


def apply_sub_task_timestamp(
    db: Session,
    *,
    sub_task_id: UUID,
    task_id: UUID,
    start_ms: Optional[int],
    end_ms: Optional[int],
    author_email: str,
) -> Tuple[Optional[int], Optional[int]]:
    validate_timestamp_pair(start_ms=start_ms, end_ms=end_ms)
    if start_ms is None and end_ms is None:
        delete_sub_task_timestamp(db=db, sub_task_id=sub_task_id)
        return None, None
    duration_ms = get_day_audio_duration_ms(db=db, task_id=task_id)
    validate_timestamp_range(start_ms=start_ms, end_ms=end_ms, duration_ms=duration_ms)
    upsert_sub_task_timestamp(
        db=db,
        sub_task_id=sub_task_id,
        start_ms=start_ms,
        end_ms=end_ms,
        created_by=author_email,
    )
    return start_ms, end_ms


def delete_plan_subtask_timestamp(token: str, sub_task_id: UUID) -> None:
    with SessionLocal() as db:
        current_author = validate_cms_author_details(token=token)
        _get_author_sub_task(db=db, sub_task_id=sub_task_id, current_author=current_author)
        delete_sub_task_timestamp(db=db, sub_task_id=sub_task_id)


def timestamp_fields_from_subtask(subtask) -> Tuple[Optional[int], Optional[int]]:
    timestamp = getattr(subtask, "timestamp", None)
    if timestamp is None:
        return None, None
    start_ms = getattr(timestamp, "start_ms", None)
    end_ms = getattr(timestamp, "end_ms", None)
    if not isinstance(start_ms, int) or not isinstance(end_ms, int):
        return None, None
    return start_ms, end_ms
