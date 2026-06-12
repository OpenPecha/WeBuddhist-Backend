from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from .accumulator_enums import AccumulatorType


class AccumulatorDTO(BaseModel):
    id: UUID
    user_id: UUID
    group_id: UUID
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


class CreateAccumulatorRequest(BaseModel):
    group_id: UUID
    name: str
    description: Optional[str] = None
    target_count: Optional[int] = None
    text_id: Optional[UUID] = None


class UpdateAccumulatorRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    target_count: Optional[int] = None
    text_id: Optional[UUID] = None


class RecordAccumulatorCountRequest(BaseModel):
    accumulator_id: UUID
    count: int = Field(..., gt=0, description="Number of counts recited in this session")


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
