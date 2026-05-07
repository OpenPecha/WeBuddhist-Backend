from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from pecha_api.plans.plans_enums import DifficultyLevel, PlanStatus,ContentType
from uuid import UUID
from datetime import datetime, date as DateType
from pecha_api.plans.plans_models import Plan

class PlanDayBasic(BaseModel):
    id: str
    day_number: int

class ImageUrlModel(BaseModel):
    thumbnail: str
    medium: str
    original: str       

class PlanDaysResponse(BaseModel):
    days: List[PlanDayBasic]

class AuthorDTO(BaseModel):
    id: UUID
    firstname: str
    lastname: str
    image: Optional[ImageUrlModel] = None


    
class PublicPlanDTO(BaseModel):
    id: UUID
    title: str
    description: str
    language: str
    difficulty_level: Optional[DifficultyLevel] = None
    image: Optional[ImageUrlModel] = None
    total_days: int
    tags: Optional[List[str]] = [],
    author: Optional[AuthorDTO] = None
    start_date: Optional[datetime] = None

class SubTaskDTO(BaseModel):
    id: UUID
    content_type: ContentType
    content: Optional[str] = None
    duration: Optional[str] = None
    image_url: Optional[str] = None
    source_text_id: Optional[UUID] = None
    pecha_segment_id: Optional[str] = None
    segment_ids: Optional[List[UUID]] = None
    display_order: Optional[int] = None

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


class PlanWithDays(BaseModel):
    id: UUID
    title: str
    description: str            
    language: str
    image: Optional[ImageUrlModel] = None
    plan_image: Optional[ImageUrlModel] = None
    total_days: int
    difficulty_level: str
    tags: List[str]
    days: List[PlanDayDTO]

class PublicPlansResponse(BaseModel):
    plans: List[PublicPlanDTO]
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

class SeriesDTO(BaseModel):
    id: UUID
    name: Optional[dict] = None
    image: Optional[ImageUrlModel] = None

class DailyPlanResponse(BaseModel):
    plan_id: UUID
    plan_title: str
    plan_description: str
    image: Optional[ImageUrlModel] = None
    series: Optional[SeriesDTO] = None
    date: DateType
    day_number: int
    total_days: int
    start_date: DateType
    end_date: DateType
    previous_date: Optional[DateType] = None
    next_date: Optional[DateType] = None
    tasks: List[TaskDTO]

class TagsResponse(BaseModel):
    tags: List[str]
    
TaskDTO.model_rebuild()
