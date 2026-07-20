from uuid import UUID

from fastapi import APIRouter, Depends
from starlette import status

from pecha_api.plans.audio.audio_job_service import (
    get_audio_job_status,
    update_audio_job_status,
)
from pecha_api.plans.audio.plan_audio_response_models import (
    AudioJobStatusResponse,
    UpdateAudioJobStatusRequest,
)
from pecha_api.routines.routine_notifications.dependencies import verify_dispatch_token

internal_audio_jobs_router = APIRouter(
    prefix="/internal/audio/jobs",
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
