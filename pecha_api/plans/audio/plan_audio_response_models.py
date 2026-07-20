from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

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


class UpdateAudioJobStatusRequest(BaseModel):
    status: AudioJobStatus
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = Field(default=None, max_length=4000)

    @model_validator(mode="after")
    def validate_status_payload(self) -> "UpdateAudioJobStatusRequest":
        if self.status == AudioJobStatus.PENDING:
            raise ValueError("Worker cannot set status to pending")
        if self.status == AudioJobStatus.COMPLETED and not self.result:
            raise ValueError("result is required when status is completed")
        if self.status == AudioJobStatus.FAILED and not self.error_message:
            raise ValueError("error_message is required when status is failed")
        return self


class AudioGenerationSubTaskDTO(BaseModel):
    id: UUID
    task_id: UUID
    content_type: str
    content: Optional[str] = None
    audio_url: Optional[str] = None
    display_order: int


class DayAudioGenerationPayload(BaseModel):
    id: UUID
    plan_id: UUID
    subtasks: List[AudioGenerationSubTaskDTO]


class SubTaskAudioGenerationPayload(BaseModel):
    id: UUID
    task_id: UUID
    content_type: str
    content: Optional[str] = None
    audio_url: Optional[str] = None


class SubTaskTimestampPayload(BaseModel):
    sub_task_id: UUID
    start_ms: int
    end_ms: int


class DayAudioGenerationResultRequest(BaseModel):
    audio_key: str
    duration_ms: int
    mime_type: str = "audio/wav"
    file_size_bytes: int
    timestamps: List[SubTaskTimestampPayload] = Field(default_factory=list)


class SubTaskAudioGenerationResultRequest(BaseModel):
    audio_key: str
    duration_ms: int
