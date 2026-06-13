from pydantic import BaseModel, model_serializer
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from pecha_api.plans.media.media_response_models import ImageUrlModel
from .routines_enums import SessionType


class SessionRequest(BaseModel):
    session_type: SessionType
    source_id: Optional[UUID] = None  
    duration_ms: Optional[int] = None  
    display_order: int


class CreateTimeBlockRequest(BaseModel):
    time: str
    time_int: int
    notification_enabled: bool = True
    sessions: List[SessionRequest]


class UpdateTimeBlockRequest(BaseModel):
    time: str
    time_int: int
    notification_enabled: bool = True
    sessions: List[SessionRequest]


class SessionDTO(BaseModel):
    id: UUID
    session_type: SessionType
    source_id: Optional[UUID] = None  
    title: Optional[str] = None  
    language: Optional[str] = None  
    duration_ms: Optional[int] = None  
    image: Optional[ImageUrlModel] = None    
    display_order: int
    start_date: Optional[datetime] = None  # Plan's start_date
    started_at: Optional[datetime] = None  # User's started_at from progress
    item_count: Optional[int] = None  # Recitation collection's item count

    @model_serializer(mode="wrap")
    def _omit_inapplicable_fields(self, serializer):
        data = serializer(self)
        if self.session_type == SessionType.TIMER:
            for field in ("source_id", "title", "language", "image", "start_date", "started_at", "item_count"):
                data.pop(field, None)
        elif self.session_type == SessionType.RECITATION_COLLECTION:
            for field in ("duration_ms", "language", "start_date", "started_at"):
                data.pop(field, None)
        elif self.session_type == SessionType.RECITATION:
            for field in ("duration_ms", "start_date", "started_at", "item_count"):
                data.pop(field, None)
        else:  # PLAN
            for field in ("duration_ms", "item_count"):
                data.pop(field, None)
        return data


class TimeBlockDTO(BaseModel):
    id: UUID
    time: str
    time_int: int
    notification_enabled: bool
    sessions: List[SessionDTO]


class RoutineWithTimeBlocksResponse(BaseModel):
    id: UUID
    time_blocks: List[TimeBlockDTO]


class RoutineResponse(BaseModel):
    id: UUID
    time_blocks: List[TimeBlockDTO]
    skip: int
    limit: int
    total: int


class RoutineInfoResponse(BaseModel):
    series_count: int
    recitation_count: int
