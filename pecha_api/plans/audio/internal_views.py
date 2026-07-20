from uuid import UUID

from fastapi import APIRouter, Depends
from starlette import status

from pecha_api.plans.audio.audio_generation_payload_service import (
    apply_day_audio_generation_result,
    apply_sub_task_audio_generation_result,
    get_day_audio_generation_payload,
    get_sub_task_audio_generation_payload,
)
from pecha_api.plans.audio.audio_job_service import (
    get_audio_job_status,
    update_audio_job_status,
)
from pecha_api.plans.audio.plan_audio_response_models import (
    AudioJobStatusResponse,
    DayAudioGenerationPayload,
    DayAudioGenerationResultRequest,
    SubTaskAudioGenerationPayload,
    SubTaskAudioGenerationResultRequest,
    UpdateAudioJobStatusRequest,
)
from pecha_api.routines.routine_notifications.dependencies import verify_dispatch_token

internal_audio_jobs_router = APIRouter(
    prefix="/internal/audio/jobs",
    tags=["Internal"],
)

internal_audio_generation_router = APIRouter(
    prefix="/internal/audio",
    tags=["Internal"],
)


@internal_audio_jobs_router.get(
    "/{job_id}",
    status_code=status.HTTP_200_OK,
    response_model=AudioJobStatusResponse,
)
def get_internal_audio_job_status(
    job_id: UUID,
    _: None = Depends(verify_dispatch_token),
) -> AudioJobStatusResponse:
    return get_audio_job_status(job_id=job_id)


@internal_audio_jobs_router.patch(
    "/{job_id}",
    status_code=status.HTTP_200_OK,
    response_model=AudioJobStatusResponse,
)
def patch_internal_audio_job_status(
    job_id: UUID,
    request: UpdateAudioJobStatusRequest,
    _: None = Depends(verify_dispatch_token),
) -> AudioJobStatusResponse:
    return update_audio_job_status(
        job_id=job_id,
        next_status=request.status,
        result=request.result,
        error_message=request.error_message,
    )


@internal_audio_generation_router.get(
    "/days/{day_id}/generation-payload",
    status_code=status.HTTP_200_OK,
    response_model=DayAudioGenerationPayload,
)
def get_internal_day_audio_generation_payload(
    day_id: UUID,
    _: None = Depends(verify_dispatch_token),
) -> DayAudioGenerationPayload:
    return get_day_audio_generation_payload(day_id=day_id)


@internal_audio_generation_router.get(
    "/sub-tasks/{sub_task_id}/generation-payload",
    status_code=status.HTTP_200_OK,
    response_model=SubTaskAudioGenerationPayload,
)
def get_internal_sub_task_audio_generation_payload(
    sub_task_id: UUID,
    _: None = Depends(verify_dispatch_token),
) -> SubTaskAudioGenerationPayload:
    return get_sub_task_audio_generation_payload(sub_task_id=sub_task_id)


@internal_audio_generation_router.post(
    "/days/{day_id}/generation-result",
    status_code=status.HTTP_204_NO_CONTENT,
)
def post_internal_day_audio_generation_result(
    day_id: UUID,
    request: DayAudioGenerationResultRequest,
    _: None = Depends(verify_dispatch_token),
) -> None:
    apply_day_audio_generation_result(day_id=day_id, request=request)


@internal_audio_generation_router.post(
    "/sub-tasks/{sub_task_id}/generation-result",
    status_code=status.HTTP_204_NO_CONTENT,
)
def post_internal_sub_task_audio_generation_result(
    sub_task_id: UUID,
    request: SubTaskAudioGenerationResultRequest,
    _: None = Depends(verify_dispatch_token),
) -> None:
    apply_sub_task_audio_generation_result(sub_task_id=sub_task_id, request=request)
