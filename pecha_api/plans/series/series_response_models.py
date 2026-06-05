from pydantic import BaseModel, field_validator
from typing import Dict, List, Optional
from uuid import UUID
from datetime import datetime

from pecha_api.plans.plans_enums import PlanStatus, DifficultyLevel, LanguageCode
from pecha_api.plans.tags.tag_response_models import TagSummaryDTO
from pecha_api.plans.media.media_response_models import ImageUrlModel


def _validate_plan_language_keys(v):
    """Reject plans dict keys that are not valid LanguageCode enum values."""
    if v is None:
        return v
    valid_codes = {code.value for code in LanguageCode}
    invalid_keys = [k for k in v.keys() if k not in valid_codes]
    if invalid_keys:
        raise ValueError(
            f"Invalid language code(s) in plans: {invalid_keys}. "
            f"Allowed: {sorted(valid_codes)}"
        )
    return v


class SeriesMetadataDTO(BaseModel):
    id: UUID
    title: str
    description: Optional[str] = None
    language: str


class SeriesMetadataInput(BaseModel):
    title: str
    description: Optional[str] = None
    language: LanguageCode


class CreateSeriesRequest(BaseModel):
    group_id: UUID
    metadata: List[SeriesMetadataInput]
    image_key: Optional[str] = None
    featured: Optional[bool] = False
    plans: Optional[Dict[str, List[UUID]]] = None

    @field_validator("plans")
    @classmethod
    def _validate_plans(cls, v):
        return _validate_plan_language_keys(v)


class UpdateSeriesRequest(BaseModel):
    metadata: Optional[List[SeriesMetadataInput]] = None
    image_key: Optional[str] = None
    featured: Optional[bool] = None
    plans: Optional[Dict[str, List[UUID]]] = None

    @field_validator("plans")
    @classmethod
    def _validate_plans(cls, v):
        return _validate_plan_language_keys(v)


class UpdateSeriesStatusRequest(BaseModel):
    status: PlanStatus


class SeriesPlanDTO(BaseModel):
    id: UUID
    title: str
    description: Optional[str] = None
    language: str
    difficulty_level: Optional[DifficultyLevel] = None
    image: Optional[ImageUrlModel] = None
    image_key: Optional[str] = None
    tags: List[TagSummaryDTO] = []
    status: PlanStatus
    featured: bool
    display_order: Optional[int] = None
    start_date: Optional[datetime] = None
    total_days: int = 0
    group_id: Optional[UUID] = None


class SeriesListItemDTO(BaseModel):
    id: UUID
    metadata: List[SeriesMetadataDTO] = []
    image: Optional[ImageUrlModel] = None
    image_key: Optional[str] = None
    author_id: UUID
    featured: bool
    status: PlanStatus
    plan_count: int = 0
    total_days: int = 0


class SeriesDTO(BaseModel):
    id: UUID
    metadata: List[SeriesMetadataDTO] = []
    image: Optional[ImageUrlModel] = None
    image_key: Optional[str] = None
    author_id: UUID
    featured: bool
    status: PlanStatus
    plans: List[SeriesPlanDTO] = []
    total_days: int = 0
    group_id: Optional[UUID] = None


class SeriesListResponse(BaseModel):
    series: list[SeriesListItemDTO]
    skip: int
    limit: int
    total: int
