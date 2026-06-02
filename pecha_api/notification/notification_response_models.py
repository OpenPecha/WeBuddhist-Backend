from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class NotificationDTO(BaseModel):
    id: UUID
    title: str
    description: Optional[str] = None
    category: str
    reference_id: Optional[UUID] = None
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime


class NotificationListResponse(BaseModel):
    notifications: List[NotificationDTO]
    skip: int
    limit: int
    total: int
