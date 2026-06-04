from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime

from pecha_api.plans.media.media_response_models import ImageUrlModel
from .routines_enums import SessionType


class SessionRequest(BaseModel):
    session_type: SessionType
    source_id: UUID
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
    source_id: UUID
    title: str
    language: str
    image: Optional[ImageUrlModel] = None
    display_order: int
    start_date: Optional[datetime] = None  # Plan's start_date
    started_at: Optional[datetime] = None  # User's started_at from progress


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
