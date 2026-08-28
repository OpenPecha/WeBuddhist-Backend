from pydantic import BaseModel
from typing import Optional
from pecha_api.plans.plans_enums import ContentType
from typing import List
from uuid import UUID


class SubTaskRequestFields(BaseModel):
    content_type: str
    content: str
    duration: Optional[str] = None
    source_text_id: Optional[str] = None
    pecha_segment_id: Optional[str] = None
    segment_ids: Optional[List[str]] = None
    segment_numbers: Optional[List[int]] = None
    start_ms: Optional[int] = None
    end_ms: Optional[int] = None


class SubTaskRequest(BaseModel):
    task_id: UUID
    sub_tasks: List[SubTaskRequestFields]


class SubTaskDTO(BaseModel):
    id: Optional[UUID]
    content_type: ContentType
    content: str
    duration: Optional[str] = None
    image_url: Optional[str] = None
    audio_url: Optional[str] = None
    source_text_id: Optional[str] = None
    pecha_segment_id: Optional[str] = None
    segment_ids: Optional[List[str]] = None
    segment_numbers: Optional[List[int]] = None
    display_order: int
    start_ms: Optional[int] = None
    end_ms: Optional[int] = None

class SubTaskResponse(BaseModel):
    sub_tasks: List[SubTaskDTO]


class UpdateSubTaskRequest(BaseModel):
    task_id: UUID
    sub_tasks: List[SubTaskDTO]

class UpdateSubTaskResponse(BaseModel):
    sub_task_id: UUID

class SubtaskOrderItem(BaseModel):
    id: UUID
    display_order: int    

class SubTaskOrderRequest(BaseModel):
    subtasks: List[SubtaskOrderItem]

class UpdatedSubtaskOrderItem(BaseModel):
    sub_task_id: UUID
    display_order: int

class SubTaskOrderResponse(BaseModel):
    updated_subtasks: List[UpdatedSubtaskOrderItem]
