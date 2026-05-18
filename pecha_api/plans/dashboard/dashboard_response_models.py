from datetime import datetime
from typing import List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from pecha_api.plans.plans_enums import PlanStatus

DashboardTab = Literal["all", "series", "plans"]
DashboardItemType = Literal["series", "plan"]


class DashboardItemDTO(BaseModel):
    id: UUID
    type: DashboardItemType
    title: str
    image_url: Optional[str] = None
    status: PlanStatus
    featured: bool
    languages: List[str] = Field(default_factory=list)
    enrolled_count: int = 0
    plans_count: Optional[int] = None
    updated_at: Optional[datetime] = None
    created_at: datetime


class DashboardPaginationDTO(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int


class DashboardItemsResponse(BaseModel):
    items: List[DashboardItemDTO]
    pagination: DashboardPaginationDTO
