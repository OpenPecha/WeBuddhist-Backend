from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from uuid import UUID
from datetime import datetime

from pecha_api.plans.plans_enums import PlanStatus, DifficultyLevel


class CreateSeriesRequest(BaseModel):
    name: Dict[str, Any]
    image_key: Optional[str] = None
    featured: Optional[bool] = False
    plans: Optional[Dict[str, List[UUID]]] = None


class SeriesPlanDTO(BaseModel):
    id: UUID
    title: str
    description: Optional[str] = None
    language: str
    difficulty_level: Optional[DifficultyLevel] = None
    image_url: Optional[str] = None
    image_key: Optional[str] = None
    tags: Optional[List[str]] = []
    status: PlanStatus
    featured: bool
    display_order: Optional[int] = None
    start_date: Optional[datetime] = None
    total_days: int = 0


class SeriesDTO(BaseModel):
    id: UUID
    name: Dict[str, Any]
    image: Optional[str] = None
    image_key: Optional[str] = None
    author_id: UUID
    featured: bool
    status: PlanStatus
    plans: List[SeriesPlanDTO] = []
    total_days: int = 0


class SeriesListResponse(BaseModel):
    series: list[SeriesDTO]
    skip: int
    limit: int
    total: int
