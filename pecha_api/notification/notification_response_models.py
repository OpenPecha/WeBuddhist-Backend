from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class NotificationActionDTO(BaseModel):
    label: str
    method: str
    path: str


class NotificationDTO(BaseModel):
    id: UUID
    title: str
    description: Optional[str] = None
    category: str
    reference_type: Optional[str] = None
    reference_id: Optional[UUID] = None
    is_read: bool
    read_at: Optional[datetime] = None
    actions: List[NotificationActionDTO] = []
    created_at: datetime


class NotificationListResponse(BaseModel):
    notifications: List[NotificationDTO]
    skip: int
    limit: int
    total: int
