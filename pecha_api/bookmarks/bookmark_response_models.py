from pydantic import BaseModel, ConfigDict, field_validator
from uuid import UUID
from typing import List, Optional
from datetime import datetime

from pecha_api.bookmarks.bookmark_enums import BookmarkType
from pecha_api.plans.public.plan_response_models import PublicPlanDTO
from pecha_api.plans.series.series_response_models import SeriesListItemDTO
from pecha_api.accumulator.accumulator_response_models import AccumulatorDTO
from pecha_api.timers.timer_response_models import TimerDTO


class CreateBookmarkRequest(BaseModel):
    type: BookmarkType
    source_id: str
    name: Optional[str] = None

    @field_validator("source_id")
    @classmethod
    def _validate_source_id(cls, value: str, info) -> str:
        value = value.strip()
        if not value:
            raise ValueError("source_id must not be empty")

        bookmark_type = info.data.get("type")
        if bookmark_type is not None and bookmark_type != BookmarkType.VERSE:
            try:
                return str(UUID(value))
            except ValueError:
                raise ValueError(f"source_id must be a valid UUID for type {bookmark_type.value}")
        return value


class BookmarkDTO(BaseModel):
    model_config = ConfigDict(ser_json_exclude_none=True)

    id: UUID
    type: BookmarkType
    source_id: str
    name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    text_id: Optional[str] = None
    text_title: Optional[str] = None
    segment_id: Optional[str] = None
    verse_id: Optional[str] = None
    segment_content: Optional[str] = None
    plan: Optional[PublicPlanDTO] = None
    series: Optional[SeriesListItemDTO] = None
    accumulator: Optional[AccumulatorDTO] = None
    timer: Optional[TimerDTO] = None


class BookmarksResponse(BaseModel):
    model_config = ConfigDict(ser_json_exclude_none=True)

    bookmarks: List[BookmarkDTO]


class BookmarkExistsQuery(BaseModel):
    type: Optional[BookmarkType] = None
    source_id: str

    @field_validator("source_id")
    @classmethod
    def _validate_source_id(cls, value: str, info) -> str:
        value = value.strip()
        if not value:
            raise ValueError("source_id must not be empty")

        bookmark_type = info.data.get("type")
        if bookmark_type is not None and bookmark_type != BookmarkType.VERSE:
            try:
                return str(UUID(value))
            except ValueError:
                raise ValueError(f"source_id must be a valid UUID for type {bookmark_type.value}")
        return value


class BookmarkExistsResponse(BaseModel):
    exists: bool
    id: Optional[UUID] = None
