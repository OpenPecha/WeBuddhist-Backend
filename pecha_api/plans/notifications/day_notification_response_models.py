from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CreateNotificationRequest(BaseModel):
    title: str = Field(..., max_length=255)
    body: str
    image_type: Optional[str] = None
    image_url: Optional[str] = None


class UpdateNotificationRequest(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    body: Optional[str] = None
    image_type: Optional[str] = None
    image_url: Optional[str] = None


class NotificationDTO(BaseModel):
    id: UUID
    day_id: UUID
    title: str
    body: str
    image_type: Optional[str] = None
    image_url: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
