import re
from pydantic import BaseModel, field_validator
from typing import Optional
from uuid import UUID
from typing import List
from pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_response_model import SubTaskDTO

_YOUTUBE_URL_PATTERN = re.compile(
    r"^https?://(www\.)?"
    r"(youtube\.com/(watch\?v=|shorts/|embed/|live/)[\w\-]+|youtu\.be/[\w\-]+)",
    re.IGNORECASE,
)


def _validate_youtube_url(value: Optional[str]) -> Optional[str]:
    """Allow None / empty (clears the video); otherwise must be a YouTube URL."""
    if value is None or value == "":
        return value
    if not _YOUTUBE_URL_PATTERN.match(value.strip()):
        raise ValueError("youtube_url must be a valid YouTube URL")
    return value.strip()


# Request/Response Models
class CreateTaskRequest(BaseModel):
    plan_id: UUID
    day_id: UUID
    title: str
    description: Optional[str] = None
    estimated_time: Optional[int] = None
    youtube_url: Optional[str] = None
    youtube_duration: Optional[str] = None

    @field_validator("youtube_url")
    @classmethod
    def _check_youtube_url(cls, value: Optional[str]) -> Optional[str]:
        return _validate_youtube_url(value)

class TaskDTO(BaseModel):
    id: UUID
    title: str
    display_order: int
    estimated_time: Optional[int] = None
    youtube_url: Optional[str] = None
    youtube_duration: Optional[str] = None

class UpdatedTaskDayResponse(BaseModel):
    task_id: UUID
    title: str
    day_id: UUID
    display_order: int
    estimated_time: Optional[int] = None

class UpdateTaskDayRequest(BaseModel):
    target_day_id: UUID

class UpdateTaskTitleRequest(BaseModel):
    title: Optional[str] = None
    youtube_url: Optional[str] = None
    youtube_duration: Optional[str] = None

    @field_validator("youtube_url")
    @classmethod
    def _check_youtube_url(cls, value: Optional[str]) -> Optional[str]:
        return _validate_youtube_url(value)

class UpdateTaskTitleResponse(BaseModel):
    task_id: UUID
    title: Optional[str] = None
    youtube_url: Optional[str] = None
    youtube_duration: Optional[str] = None

class TaskOrderItem(BaseModel):
    id: UUID
    display_order: int

class UpdateTaskOrderRequest(BaseModel):
    tasks: List[TaskOrderItem]
    
class UpdatedTaskOrderResponse(BaseModel):
    updated_tasks: List[TaskOrderItem]
    
class GetTaskRequest(BaseModel):
    task_id: UUID

class GetTaskResponse(BaseModel):
    id: UUID
    title: str
    display_order: int
    estimated_time: Optional[int] = None
    youtube_url: Optional[str] = None
    youtube_duration: Optional[str] = None
    subtasks: List[SubTaskDTO]

class ContentAndImageUrl(BaseModel):
    content: str
    image_url: Optional[str] = None