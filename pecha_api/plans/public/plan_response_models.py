from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from pecha_api.plans.plans_enums import DifficultyLevel, PlanStatus,ContentType
from uuid import UUID
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

class SubTaskDTO(BaseModel):
    id: UUID
    content_type: ContentType
    content: Optional[str] = None
    display_order: Optional[int] = None
    source_text_id: Optional[UUID] = None
    pecha_segment_id: Optional[str] = None

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

class TagsResponse(BaseModel):
    tags: List[str]
    
TaskDTO.model_rebuild()
