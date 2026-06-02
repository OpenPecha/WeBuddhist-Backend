from typing import Optional

from pydantic import BaseModel
from pecha_api.plans.response_message import IMAGE_UPLOAD_SUCCESS
from pecha_api.plans.shared.models import ImageUrlModel

class PlanUploadResponse(BaseModel):
    image: ImageUrlModel
    key: str
    path: str
    message: str = IMAGE_UPLOAD_SUCCESS


class TextImageUploadResponse(BaseModel):
    id: str
    text_id: str
    image: ImageUrlModel
    key: str
    path: str
    message: str = IMAGE_UPLOAD_SUCCESS


class PlanDayAudioUploadResponse(BaseModel):
    plan_item_id: str
    audio_key: str
    audio_url: str
    duration_ms: Optional[int] = None
    message: str


class Error(BaseModel):
    error: str
    message: str