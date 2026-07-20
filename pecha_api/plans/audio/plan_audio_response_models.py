from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel

from pecha_api.plans.plans_enums import AudioJobStatus


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


class AssignPlanDayAudioRequest(BaseModel):
    audio_key: str
    duration_ms: Optional[int] = None


class AudioJobAcceptedResponse(BaseModel):
    job_id: UUID
    status: AudioJobStatus = AudioJobStatus.PENDING


class AudioJobStatusResponse(BaseModel):
    job_id: UUID
    status: AudioJobStatus
    day_id: Optional[UUID] = None
    sub_task_id: Optional[UUID] = None
    language: str
    type: str
    voice_name: str
    audio_url: Optional[str] = None
    audio_duration_ms: Optional[int] = None
    s3_key: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
