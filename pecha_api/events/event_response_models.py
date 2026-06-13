from pydantic import BaseModel, field_validator, model_validator
from typing import Optional, List, Union
from datetime import datetime
from uuid import UUID

from pecha_api.plans.plans_enums import LanguageCode
from pecha_api.plans.media.media_response_models import ImageUrlModel


class EventMetadataDTO(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    language: str


EventMetadataResponse = Union[EventMetadataDTO, List[EventMetadataDTO], None]


class EventMetadataInput(BaseModel):
    name: str
    description: Optional[str] = None
    language: LanguageCode


def _validate_unique_languages(metadata: List[EventMetadataInput]) -> List[EventMetadataInput]:
    languages = [entry.language.value for entry in metadata]
    if len(languages) != len(set(languages)):
        raise ValueError("Duplicate languages in metadata are not allowed")
    return metadata


def _validate_date_range(start_date: datetime, end_date: datetime) -> None:
    if end_date < start_date:
        raise ValueError("end_date must be greater than or equal to start_date")


class EventDTO(BaseModel):
    id: UUID
    plan_id: Optional[UUID] = None
    accumulator_id: Optional[UUID] = None
    mantra_id: Optional[UUID] = None
    timer_id: Optional[UUID] = None
    group_id: UUID
    start_date: datetime
    end_date: datetime
    is_one_day: bool
    metadata: EventMetadataResponse
    image: Optional[ImageUrlModel] = None
    image_url: Optional[str] = None
    created_at: datetime
    created_by: str
    updated_at: Optional[datetime] = None


class EventsResponse(BaseModel):
    events: List[EventDTO]
    total: int
    skip: int
    limit: int


class CreateEventRequest(BaseModel):
    group_id: UUID
    start_date: datetime
    end_date: datetime
    metadata: List[EventMetadataInput]
    image_url: Optional[str] = None
    plan_id: Optional[UUID] = None
    accumulator_id: Optional[UUID] = None
    mantra_id: Optional[UUID] = None
    timer_id: Optional[UUID] = None

    @field_validator("metadata")
    @classmethod
    def validate_metadata_not_empty(cls, value: List[EventMetadataInput]) -> List[EventMetadataInput]:
        if not value:
            raise ValueError("At least one metadata entry is required")
        return _validate_unique_languages(value)

    @model_validator(mode="after")
    def validate_dates(self) -> "CreateEventRequest":
        _validate_date_range(self.start_date, self.end_date)
        return self


class UpdateEventRequest(BaseModel):
    group_id: Optional[UUID] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    metadata: Optional[List[EventMetadataInput]] = None
    image_url: Optional[str] = None
    plan_id: Optional[UUID] = None
    accumulator_id: Optional[UUID] = None
    mantra_id: Optional[UUID] = None
    timer_id: Optional[UUID] = None

    @field_validator("metadata")
    @classmethod
    def validate_metadata_languages(cls, value: Optional[List[EventMetadataInput]]) -> Optional[List[EventMetadataInput]]:
        if value is None:
            return value
        if not value:
            raise ValueError("Metadata list cannot be empty when provided")
        return _validate_unique_languages(value)
