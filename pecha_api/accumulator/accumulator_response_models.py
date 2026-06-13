from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from .accumulator_enums import AccumulatorType


class AccumulatorDTO(BaseModel):
    id: UUID
    user_id: UUID
    group_id: Optional[UUID] = None
    type: AccumulatorType
    name: str
    description: Optional[str] = None
    target_count: Optional[int] = None
    current_count: int
    text_id: Optional[UUID] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class AccumulatorsResponse(BaseModel):
    accumulators: List[AccumulatorDTO]
    total: int
    skip: int
    limit: int


class PublicAccumulatorDTO(BaseModel):
    """Accumulator shape for the public list endpoint: omits user_id so other
    users' ids are not disclosed. group_id is kept for future CMS grouping."""
    id: UUID
    group_id: Optional[UUID] = None
    type: AccumulatorType
    name: str
    description: Optional[str] = None
    target_count: Optional[int] = None
    current_count: int
    text_id: Optional[UUID] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class PublicAccumulatorsResponse(BaseModel):
    accumulators: List[PublicAccumulatorDTO]
    total: int
    skip: int
    limit: int


class CreateAccumulatorRequest(BaseModel):
    name: str
    description: Optional[str] = None
    target_count: Optional[int] = None
    current_count: int = Field(0, ge=0, description="Initial count to seed the accumulator with")
    text_id: Optional[UUID] = None


class UpdateAccumulatorRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    target_count: Optional[int] = None
    current_count: Optional[int] = Field(None, ge=0, description="New absolute current count")
    text_id: Optional[UUID] = None


class AccumulatorSessionDTO(BaseModel):
    count: int
    created_at: datetime


class AccumulatorHistoryDTO(BaseModel):
    accumulator_id: UUID
    name: str
    description: Optional[str] = None
    target_count: Optional[int] = None
    current_count: int
    total_counted: int
    sessions: List[AccumulatorSessionDTO]


class AccumulatorHistoryResponse(BaseModel):
    accumulators: List[AccumulatorHistoryDTO]
    total: int
    skip: int
    limit: int
