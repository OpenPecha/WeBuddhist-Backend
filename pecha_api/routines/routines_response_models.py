from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID

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


class SessionDTO(BaseModel):
    id: UUID
    session_type: SessionType
    source_id: UUID
    title: str
    language: str
    image_url: Optional[str] = None
    display_order: int


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
