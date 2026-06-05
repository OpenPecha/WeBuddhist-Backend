from datetime import datetime
from typing import List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field, model_serializer

from pecha_api.plans.media.media_response_models import ImageUrlModel
from pecha_api.plans.plans_enums import PlanStatus
from pecha_api.plans.series.series_response_models import SeriesMetadataDTO, SeriesPlanDTO

DashboardTab = Literal["all", "series", "plans"]
DashboardItemType = Literal["series", "plan"]


class DashboardItemDTO(BaseModel):
    id: UUID
    type: DashboardItemType
    title: Optional[str] = None
    metadata: Optional[List[SeriesMetadataDTO]] = None
    plans: Optional[List[SeriesPlanDTO]] = None
    author_id: Optional[UUID] = None
    image: Optional[ImageUrlModel] = None
    image_key: Optional[str] = None
    status: PlanStatus
    featured: bool
    languages: List[str] = Field(default_factory=list)
    enrolled_count: int = 0
    plans_count: Optional[int] = None
    updated_at: Optional[datetime] = None
    created_at: datetime

    @model_serializer(mode="wrap")
    def _omit_title_for_series(self, serializer):
        data = serializer(self)
        if self.type == "series":
            data.pop("title", None)
        if self.plans is None:
            data.pop("plans", None)
        return data


class DashboardPaginationDTO(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int


class DashboardItemsResponse(BaseModel):
    items: List[DashboardItemDTO]
    pagination: DashboardPaginationDTO
