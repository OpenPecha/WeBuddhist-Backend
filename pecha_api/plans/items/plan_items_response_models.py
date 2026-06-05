from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from typing import List


class ItemDBInput(BaseModel):
    plan_id: UUID
    day_number: int

class ItemDTO(BaseModel):
    id: UUID
    plan_id: UUID
    day_number: int
    audio_url: Optional[str] = None

class UpdateDayRequest(BaseModel):
    day_number: int

class ItemDayNumberDTO(BaseModel):
    id: UUID
    day_number: int

class ReorderDaysRequest(BaseModel):
    days: List[ItemDayNumberDTO]

class CreateDaysRequest(BaseModel):
    number_of_days: int = Field(default=1, ge=1)
    source_day_id: Optional[UUID] = None

class DeleteDaysRequest(BaseModel):
    day_ids: List[UUID]