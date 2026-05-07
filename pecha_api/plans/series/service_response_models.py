from pydantic import BaseModel
from typing import Any, Dict, Optional
from uuid import UUID

from pecha_api.plans.plans_enums import PlanStatus


class CreateSeriesRequest(BaseModel):
    name: Dict[str, Any]
    author_id: UUID
    created_by: str
    image: Optional[str] = None
    featured: Optional[bool] = False


class SeriesDTO(BaseModel):
    id: UUID
    name: Dict[str, Any]
    image: Optional[str] = None
    image_key: Optional[str] = None
    author_id: UUID
    featured: bool
    status: PlanStatus


class SeriesListResponse(BaseModel):
    series: list[SeriesDTO]
    skip: int
    limit: int
    total: int
