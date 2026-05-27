from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from pecha_api.plans.plans_enums import DifficultyLevel, PlanStatus,ContentType
from uuid import UUID
from pecha_api.plans.plans_models import Plan
from pecha_api.plans.tags.tag_response_models import TagSummaryDTO


class CreatePlanRequest(BaseModel):
    title: str
    description: str
    difficulty_level: DifficultyLevel
    total_days: int
    language: str
    image_url: Optional[str] = None
    tag_ids: Optional[List[UUID]] = []
    start_date: Optional[datetime] = None
    series_id: Optional[UUID] = None
    display_order: Optional[int] = None

class UpdatePlanRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    language: Optional[str] = None
    difficulty_level: Optional[DifficultyLevel] = None
    total_days: Optional[int] = None
    image_url: Optional[str] = None
    tag_ids: Optional[List[UUID]] = None
    start_date: Optional[datetime] = None
    series_id: Optional[UUID] = None
    display_order: Optional[int] = None

class PlanStatusUpdate(BaseModel):
    status: PlanStatus

class AuthorDTO(BaseModel):
    id: UUID
    firstname: str
    lastname: str
    image_url: Optional[str] = None 
    image_key: Optional[str] = None  

class PlanDTO(BaseModel):
    id: UUID
    title: str
    description: str
    language: str
    difficulty_level: Optional[DifficultyLevel] = None
    image_url: Optional[str] = None
    image_key: Optional[str] = None
    total_days: int
    tags: List[TagSummaryDTO] = []
    status: PlanStatus
    featured: Optional[bool] = False
    subscription_count: int
    author: Optional[AuthorDTO] = None
    start_date: Optional[datetime] = None
    series_id: Optional[UUID] = None
    display_order: Optional[int] = None

class SubTaskDTO(BaseModel):
    id: UUID
    content_type: ContentType
    content: Optional[str] = None
    display_order: Optional[int] = None
    start_ms: Optional[int] = None
    end_ms: Optional[int] = None

class TaskDTO(BaseModel):
    id: UUID
    title: Optional[str] = None 
    estimated_time: Optional[int] = None
    display_order: Optional[int] = None
    subtasks: List[SubTaskDTO] = []

class PlanDayDTO(BaseModel):
    id: UUID
    day_number: int
    tasks: List[TaskDTO]
    audio_url: Optional[str] = None
    audio_duration_ms: Optional[int] = None
    audio_key: Optional[str] = None
    has_audio: Optional[bool] = None


class PlanWithDays(BaseModel):
    id: UUID
    title: str
    description: str            
    language: str
    image_url: Optional[str] = None
    plan_image_url: Optional[str] = None
    total_days: int
    difficulty_level: str
    tags: List[TagSummaryDTO] = []
    status: PlanStatus
    days: List[PlanDayDTO]
    start_date: Optional[datetime] = None
    series_id: Optional[UUID] = None
    display_order: Optional[int] = None

class PlansResponse(BaseModel):
    plans: List[PlanDTO]
    skip: int
    limit: int
    total: int

class PlanWithAggregates(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    plan: Plan
    total_days: int
    subscription_count: int

class PlansRepositoryResponse(BaseModel):
    plan_info: List[PlanWithAggregates]
    total: int

TaskDTO.model_rebuild()
