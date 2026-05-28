from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class PlanAudioDTO(BaseModel):
    id: UUID
    audio_key: str
    file_name: str
    audio_url: str
    duration_ms: Optional[int] = None
    mime_type: Optional[str] = None
    file_size_bytes: Optional[int] = None
    plan_item_id: UUID
    plan_id: UUID
    day_number: int
    created_at: datetime


class PlanAudioListResponse(BaseModel):
    audio: List[PlanAudioDTO]
    skip: int
    limit: int
    total: int
