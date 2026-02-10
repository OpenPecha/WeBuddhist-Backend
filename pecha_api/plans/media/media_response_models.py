from pydantic import BaseModel
from pecha_api.plans.response_message import IMAGE_UPLOAD_SUCCESS

class ImageUrlModel(BaseModel):
    thumbnail: str
    medium: str
    original: str

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


class Error(BaseModel):
    error: str
    message: str