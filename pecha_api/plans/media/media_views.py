from fastapi import APIRouter, UploadFile, File, status, Depends, Query, Form
from uuid import UUID
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .media_services import upload_plan_image, upload_series_image, upload_text_image
from .media_response_models import PlanUploadResponse, TextImageUploadResponse, PlanDayAudioUploadResponse, SubTaskAudioUploadResponse
from pecha_api.plans.shareable_images.day_shareable_image_enums import DayShareableImageType
from pecha_api.plans.shareable_images.day_shareable_image_response_models import PlanDayShareableImageUploadResponse
from pecha_api.plans.shareable_images.day_shareable_image_service import upload_plan_day_shareable_image
from pecha_api.plans.audio.plan_day_audio_service import upload_plan_day_audio
from pecha_api.plans.audio.plan_subtask_audio_service import upload_plan_subtask_audio
from typing import Annotated, Optional

oauth2_scheme = HTTPBearer()

media_router = APIRouter(
    prefix="/cms/media",
    tags=["Media"]
)


@media_router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_media_image(authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)], plan_id: Optional[str] = Query(None), file: UploadFile = File(...)) -> PlanUploadResponse:
    return upload_plan_image(token=authentication_credential.credentials, plan_id=plan_id, file=file)


@media_router.post("/upload/series", status_code=status.HTTP_201_CREATED)
async def upload_series_media_image(
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
    series_id: Optional[str] = Query(None),
    file: UploadFile = File(...),
) -> PlanUploadResponse:
    return upload_series_image(
        token=authentication_credential.credentials,
        series_id=series_id,
        file=file,
    )


@media_router.post("/upload/text", status_code=status.HTTP_201_CREATED)
async def upload_text_media_image(authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)], text_id: str = Form(...), file: UploadFile = File(...)) -> TextImageUploadResponse:
    return await upload_text_image(token=authentication_credential.credentials, text_id=text_id, file=file)


@media_router.post("/upload/day-audio", status_code=status.HTTP_201_CREATED)
async def upload_day_audio(
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
    day_id: UUID = Query(...),
    duration_ms: Optional[int] = Form(None),
    file: UploadFile = File(...),
) -> PlanDayAudioUploadResponse:
    return upload_plan_day_audio(
        token=authentication_credential.credentials,
        day_id=day_id,
        file=file,
        duration_ms=duration_ms,
    )


@media_router.post("/upload/subtask-audio", status_code=status.HTTP_201_CREATED)
async def upload_subtask_audio(
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
    sub_task_id: UUID = Query(...),
    duration_ms: Optional[int] = Form(None),
    file: UploadFile = File(...),
) -> SubTaskAudioUploadResponse:
    return upload_plan_subtask_audio(
        token=authentication_credential.credentials,
        sub_task_id=sub_task_id,
        file=file,
        duration_ms=duration_ms,
    )


@media_router.post("/upload/day-shareable-image", status_code=status.HTTP_201_CREATED)
async def upload_day_shareable_image(
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
    day_id: UUID = Query(...),
    image_type: DayShareableImageType = Query(...),
    file: UploadFile = File(...),
) -> PlanDayShareableImageUploadResponse:
    return upload_plan_day_shareable_image(
        token=authentication_credential.credentials,
        day_id=day_id,
        image_type=image_type,
        file=file,
    )
