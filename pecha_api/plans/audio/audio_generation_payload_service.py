from typing import List
from uuid import UUID

from fastapi import HTTPException
from starlette import status

from pecha_api.db.database import SessionLocal
from pecha_api.plans.audio.plan_audio_response_models import (
    AudioGenerationSubTaskDTO,
    DayAudioGenerationPayload,
    DayAudioGenerationResultRequest,
    SubTaskAudioGenerationPayload,
    SubTaskAudioGenerationResultRequest,
)
from pecha_api.plans.audio.plan_item_audio_models import PlanItemAudio
from pecha_api.plans.audio.plan_item_audio_repository import upsert_plan_item_audio
from pecha_api.plans.audio.sub_task_timestamps_repository import upsert_sub_task_timestamp
from pecha_api.plans.items.plan_items_repository import get_plan_day_by_id_any_plan
from pecha_api.plans.plans_enums import ContentType
from pecha_api.plans.public.plans_cache_service import (
    schedule_invalidate_plan_day_cache_for_day,
    schedule_invalidate_plan_day_cache_for_task,
)
from pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_repository import get_sub_task_by_subtask_id
from pecha_api.plans.auth.plan_auth_models import ResponseError
from pecha_api.plans.response_message import BAD_REQUEST

_TTS_CONTENT_TYPES = {ContentType.TEXT, ContentType.SOURCE_REFERENCE}


def _content_type_value(content_type) -> str:
    if isinstance(content_type, ContentType):
        return content_type.value
    if hasattr(content_type, "value"):
        return str(content_type.value)
    return str(content_type)


def _is_tts_content_type(content_type) -> bool:
    if isinstance(content_type, ContentType):
        return content_type in _TTS_CONTENT_TYPES
    value = _content_type_value(content_type)
    return value in {ContentType.TEXT.value, ContentType.SOURCE_REFERENCE.value}


def get_day_audio_generation_payload(day_id: UUID) -> DayAudioGenerationPayload:
    with SessionLocal() as db:
        plan_item = get_plan_day_by_id_any_plan(db=db, day_id=day_id)
        tasks = sorted(plan_item.tasks or [], key=lambda task: task.display_order or 0)
        subtasks: List[AudioGenerationSubTaskDTO] = []
        for task in tasks:
            ordered_subtasks = sorted(
                task.sub_tasks or [],
                key=lambda subtask: subtask.display_order or 0,
            )
            for subtask in ordered_subtasks:
                if not _is_tts_content_type(subtask.content_type):
                    continue
                subtasks.append(
                    AudioGenerationSubTaskDTO(
                        id=subtask.id,
                        task_id=subtask.task_id,
                        content_type=_content_type_value(subtask.content_type),
                        content=subtask.content,
                        audio_url=subtask.audio_url,
                        display_order=subtask.display_order,
                    )
                )
        return DayAudioGenerationPayload(
            id=plan_item.id,
            plan_id=plan_item.plan_id,
            subtasks=subtasks,
        )


def get_sub_task_audio_generation_payload(sub_task_id: UUID) -> SubTaskAudioGenerationPayload:
    with SessionLocal() as db:
        subtask = get_sub_task_by_subtask_id(db=db, id=sub_task_id)
        if not subtask:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ResponseError(error=BAD_REQUEST, message="Sub task not found").model_dump(),
            )
        if not _is_tts_content_type(subtask.content_type):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ResponseError(
                    error=BAD_REQUEST,
                    message="Sub task content type must be TEXT or SOURCE_REFERENCE for audio generation",
                ).model_dump(),
            )
        return SubTaskAudioGenerationPayload(
            id=subtask.id,
            task_id=subtask.task_id,
            content_type=_content_type_value(subtask.content_type),
            content=subtask.content,
            audio_url=subtask.audio_url,
        )


def apply_day_audio_generation_result(
    day_id: UUID,
    request: DayAudioGenerationResultRequest,
) -> None:
    with SessionLocal() as db:
        plan_item = get_plan_day_by_id_any_plan(db=db, day_id=day_id)
        for timestamp in request.timestamps:
            upsert_sub_task_timestamp(
                db=db,
                sub_task_id=timestamp.sub_task_id,
                start_ms=timestamp.start_ms,
                end_ms=timestamp.end_ms,
                created_by="system",
            )
        upsert_plan_item_audio(
            db=db,
            plan_item_audio=PlanItemAudio(
                plan_item_id=plan_item.id,
                audio_key=request.audio_key,
                duration_ms=request.duration_ms,
                mime_type=request.mime_type,
                file_size_bytes=request.file_size_bytes,
                created_by="system",
            ),
        )
        schedule_invalidate_plan_day_cache_for_day(db=db, day_id=plan_item.id)


def apply_sub_task_audio_generation_result(
    sub_task_id: UUID,
    request: SubTaskAudioGenerationResultRequest,
) -> None:
    with SessionLocal() as db:
        subtask = get_sub_task_by_subtask_id(db=db, id=sub_task_id)
        if not subtask:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ResponseError(error=BAD_REQUEST, message="Sub task not found").model_dump(),
            )
        subtask.audio_url = request.audio_key
        subtask.duration = str(request.duration_ms)
        db.commit()
        upsert_sub_task_timestamp(
            db=db,
            sub_task_id=sub_task_id,
            start_ms=0,
            end_ms=request.duration_ms,
            created_by="system",
        )
        schedule_invalidate_plan_day_cache_for_task(db=db, task_id=subtask.task_id)
