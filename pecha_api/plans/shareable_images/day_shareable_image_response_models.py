from pydantic import BaseModel

from pecha_api.plans.response_message import IMAGE_UPLOAD_SUCCESS


class PlanDayShareableImageUploadResponse(BaseModel):
    plan_item_id: str
    image_type: str
    image_key: str
    image_url: str
    message: str = IMAGE_UPLOAD_SUCCESS
