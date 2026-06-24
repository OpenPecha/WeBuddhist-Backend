from pydantic import BaseModel, field_validator, model_validator
from typing import Dict, List, Optional, Union
from uuid import UUID
from datetime import datetime

from pecha_api.plans.plans_enums import PlanStatus, DifficultyLevel, LanguageCode
from pecha_api.plans.tags.tag_response_models import TagSummaryDTO
from pecha_api.plans.media.media_response_models import ImageUrlModel
from pecha_api.plans.groups.group_summary_models import AuthorGroupSummaryDTO


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
    sub_title: Optional[str] = None
    description: Optional[str] = None
    language: str


SeriesMetadataResponse = Union[SeriesMetadataDTO, List[SeriesMetadataDTO], None]


class SeriesMetadataInput(BaseModel):
    title: str
    sub_title: Optional[str] = None
    description: Optional[str] = None
    language: LanguageCode


class CreateSeriesRequest(BaseModel):
    group_id: UUID
    parent_series_id: Optional[UUID] = None
    metadata: Optional[List[SeriesMetadataInput]] = None
    image_key: Optional[str] = None
    featured: Optional[bool] = False
    plans: Optional[Dict[str, List[UUID]]] = None

    @field_validator("plans")
    @classmethod
    def _validate_plans(cls, v):
        return _validate_plan_language_keys(v)

    @property
    def is_clone(self) -> bool:
        return self.parent_series_id is not None

    @model_validator(mode="after")
    def _validate_mode(self):
        # Clone mode: copy everything from the parent series, so metadata/plans
        # must not be supplied in the body. Create mode: metadata is required.
        if self.parent_series_id is not None:
            if self.metadata or self.plans:
                raise ValueError(
                    "When cloning a series (parent_series_id set), metadata and plans "
                    "must not be provided; they are copied from the parent series."
                )
        elif not self.metadata:
            raise ValueError("metadata is required when creating a new series")
        return self


class UpdateSeriesRequest(BaseModel):
    metadata: Optional[List[SeriesMetadataInput]] = None
    image_key: Optional[str] = None
    featured: Optional[bool] = None
    plans: Optional[Dict[str, List[UUID]]] = None

    @field_validator("plans")
    @classmethod
    def _validate_plans(cls, v):
        return _validate_plan_language_keys(v)


class CloneSeriesPlansRequest(BaseModel):
    source_language: LanguageCode
    target_language: LanguageCode

    @model_validator(mode="after")
    def _validate_languages(self):
        if self.source_language == self.target_language:
            raise ValueError("source_language and target_language must be different")
        return self


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
    metadata: SeriesMetadataResponse = []
    image: Optional[ImageUrlModel] = None
    image_key: Optional[str] = None
    author_id: UUID
    featured: bool
    status: PlanStatus
    plan_count: int = 0
    total_days: int = 0
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    enrolled_count: int = 0
    group: Optional[AuthorGroupSummaryDTO] = None


class SeriesDTO(BaseModel):
    id: UUID
    metadata: SeriesMetadataResponse = []
    image: Optional[ImageUrlModel] = None
    image_key: Optional[str] = None
    author_id: UUID
    group_id: Optional[UUID] = None
    parent_series_id: Optional[UUID] = None
    featured: bool
    status: PlanStatus
    plans: List[SeriesPlanDTO] = []
    total_days: int = 0
    enrolled_count: int = 0
    group: Optional[AuthorGroupSummaryDTO] = None


class SeriesListResponse(BaseModel):
    series: list[SeriesListItemDTO]
    skip: int
    limit: int
    total: int
