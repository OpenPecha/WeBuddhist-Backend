from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class CreateGroupAccumulatorRequest(BaseModel):
    accumulator_id: Optional[UUID] = None
    target_count: Optional[int] = Field(None, ge=1)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class UpdateGroupAccumulatorRequest(BaseModel):
    accumulator_id: Optional[UUID] = None
    target_count: Optional[int] = Field(None, ge=1)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class GroupAccumulatorDTO(BaseModel):
    id: UUID
    accumulator_id: Optional[UUID] = None
    group_id: UUID
    target_count: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class GroupAccumulatorsResponse(BaseModel):
    accumulators: List[GroupAccumulatorDTO]
    total: int
    skip: int
    limit: int


class SubmitGroupCountRequest(BaseModel):
    current_count: int = Field(..., ge=0, description="User's new absolute current count")


class GroupAccumulatorHistoryItemDTO(BaseModel):
    id: Optional[UUID] = Field(None, description="History entry ID. None if no history was created (e.g., zero delta)")
    user_id: UUID
    count: int
    created_at: datetime


class GroupAccumulatorDetailDTO(BaseModel):
    id: UUID
    accumulator_id: Optional[UUID] = None
    group_id: UUID
    target_count: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    total_count: int = Field(..., description="Total count from all users")
    created_at: datetime
    updated_at: Optional[datetime] = None


class GroupAccumulatorHistoryResponse(BaseModel):
    group_accumulator: GroupAccumulatorDetailDTO
    history: List[GroupAccumulatorHistoryItemDTO]
    total: int
    skip: int
    limit: int
