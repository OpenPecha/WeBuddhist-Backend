from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class PlanVideoDTO(BaseModel):
    id: UUID
    plan_id: UUID
    url: str
    video_id: Optional[str] = None
    title: Optional[str] = None
    display_order: int
    created_at: Optional[datetime] = None


class PlanVideoListResponse(BaseModel):
    videos: List[PlanVideoDTO]


class CreatePlanVideoRequest(BaseModel):
    url: str
    title: Optional[str] = None


class PlanVideoOrderItem(BaseModel):
    id: UUID
    display_order: int


class ReorderPlanVideosRequest(BaseModel):
    videos: List[PlanVideoOrderItem]
