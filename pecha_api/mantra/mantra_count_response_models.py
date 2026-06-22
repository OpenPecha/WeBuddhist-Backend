from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class MantraCountSummaryDTO(BaseModel):
    mantra_id: UUID
    mantra_title: Optional[str] = None
    mala_image_id: Optional[UUID] = None
    mala_image_url: Optional[str] = None
    private_count: int
    allocated_count: int
    total_count: int
    updated_at: Optional[datetime] = None


class MantraCountsResponse(BaseModel):
    counts: List[MantraCountSummaryDTO]
    total: int
    skip: int
    limit: int


class MantraGroupAllocationDTO(BaseModel):
    group_id: UUID
    group_title: Optional[str] = None
    count: int


class MantraCountDetailDTO(BaseModel):
    mantra_id: UUID
    mantra_title: Optional[str] = None
    private_count: int
    allocated_count: int
    total_count: int
    allocations: List[MantraGroupAllocationDTO] = []
    updated_at: Optional[datetime] = None
