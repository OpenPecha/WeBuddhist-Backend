from pydantic import BaseModel
from typing import List
from uuid import UUID
from datetime import date


class CreateChantCompletionRequest(BaseModel):
    """Request to log a chant completion"""
    chant_id: UUID


class TodayChantCompletionsResponse(BaseModel):
    """Response containing list of completed chant IDs for today"""
    completed_chant_ids: List[UUID]
    date: str


class ChantCompletionDayCountResponse(BaseModel):
    """Response containing the number of unique days the user completed at least one chant in the collection"""
    collection_id: UUID
    day_count: int
