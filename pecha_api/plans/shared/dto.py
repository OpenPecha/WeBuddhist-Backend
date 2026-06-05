from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from pecha_api.plans.media.media_response_models import ImageUrlModel


class UserInfoBriefDTO(BaseModel):
    id: UUID
    firstname: str
    lastname: Optional[str] = None
    username: Optional[str] = None
    avatar_url: Optional[str] = None


class SeriesPlanBriefDTO(BaseModel):
    id: UUID
    title: str
    image: Optional[ImageUrlModel] = None
    display_order: Optional[int] = None
    total_days: int = 0
    is_completed: bool = False
    started_at: Optional[datetime] = None
    status: Optional[str] = None
