from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from .timer_enums import TimerType


class TimerDTO(BaseModel):
    id: UUID
    user_id: UUID
    group_id: UUID
    type: TimerType
    name: str
    description: Optional[str] = None
    duration: int
    audio_url: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class TimersResponse(BaseModel):
    timers: List[TimerDTO]
    total: int
    skip: int
    limit: int
