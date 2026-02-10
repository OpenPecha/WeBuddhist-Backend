from typing import List, Optional
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from pecha_api.plans.plans_enums import ContentType



class UserPlanEnrollRequest(BaseModel):
    plan_id: UUID


class UserPlanStatus(BaseModel):
    status: str  # not_started, active, paused, completed, abandoned


class UserPlanDayCompletionStatus(BaseModel):
    day_number: int
    is_completed: bool

class UserPlanDayCompletionStatusResponse(BaseModel):
    days: List[UserPlanDayCompletionStatus]

class UserPlanProgressResponse(BaseModel):
    id: UUID
    user_id: UUID
    plan_id: UUID
    plan: dict  # Will contain plan details
    started_at: datetime
    streak_count: int
    longest_streak: int
    status: str
    is_completed: bool
    completed_at: Optional[datetime] = None
    created_at: datetime

class EnrolledUserPlan(BaseModel):
    user_id: UUID
    plan_id: UUID
    streak_count: int
    longest_streak: int
    status: str
    created_at: datetime
    is_completed: bool

class UserPlanDTO(BaseModel):
    id: UUID
    title: str
    description: str
    language: str
    difficulty_level: str
    image_url: str
    started_at: datetime
    total_days: int
    tags: List[str]


class UserPlansResponse(BaseModel):
    plans: List[UserPlanDTO]
    skip: int
    limit: int
    total: int


class UserPlanProgressUpdate(BaseModel):
    status: str

class UserSubTaskDTO(BaseModel):
    id: UUID
    display_order: Optional[int] = None
    is_completed: bool
    duration: Optional[str] = None
    content_type: ContentType
    content: str
    source_text_id: Optional[UUID] = None
    pecha_segment_id: Optional[str] = None

class UserTaskDTO(BaseModel):
    id: UUID
    title: str
    estimated_time: Optional[int] = None
    display_order: int
    is_completed: bool
    sub_tasks: List[UserSubTaskDTO] = []

class UserPlanDayDetailsResponse(BaseModel):
    id: UUID
    day_number: int
    tasks: List[UserTaskDTO]
    is_completed: bool