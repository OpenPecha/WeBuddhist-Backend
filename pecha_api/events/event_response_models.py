from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from typing import Optional, List, Union
from datetime import datetime, timezone
from urllib.parse import urlparse
from uuid import UUID

from pecha_api.plans.plans_enums import LanguageCode
from pecha_api.plans.media.media_response_models import ImageUrlModel
from .location_response_models import LocationDTO
from .event_enums import RecurrenceFrequency, RecurrenceDateSystem


class EventMetadataDTO(BaseModel):
    model_config = ConfigDict(ser_json_exclude_none=True)

    id: UUID
    name: str
    description: Optional[str] = None
    language: str


EventMetadataResponse = Union[EventMetadataDTO, List[EventMetadataDTO], None]


class EventLinkDTO(BaseModel):
    model_config = ConfigDict(ser_json_exclude_none=True)

    id: UUID
    type: str
    url: str
    label: Optional[str] = None
    display_order: int


def _validate_link_url(url: str) -> str:
    parsed = urlparse(url.strip())
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError("url must be a valid http or https URL")
    return url.strip()


class EventLinkInput(BaseModel):
    type: str = Field(max_length=50)
    url: str = Field(max_length=2000)
    label: Optional[str] = Field(default=None, max_length=255)
    display_order: int = 1

    @field_validator("type")
    @classmethod
    def validate_type_not_empty(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("type must be a non-empty string")
        return value.strip()

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        return _validate_link_url(value)


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


class RecurrenceInput(BaseModel):
    frequency: RecurrenceFrequency
    date_system: RecurrenceDateSystem
    calendar_type: Optional[str] = Field(None, max_length=10)
    month: Optional[int] = Field(None, ge=1, le=12)
    day: int = Field(ge=1, le=31)
    duration_days: int = Field(default=1, ge=1)

    @model_validator(mode="after")
    def validate_recurrence_rules(self) -> "RecurrenceInput":
        if self.date_system == RecurrenceDateSystem.TIBETAN_LUNAR:
            if not self.calendar_type:
                raise ValueError("calendar_type is required for TIBETAN_LUNAR date system")
            if self.calendar_type not in ("phugpa", "tsurphu"):
                raise ValueError("calendar_type must be 'phugpa' or 'tsurphu'")
            if self.day > 30:
                raise ValueError("Lunar day must be between 1 and 30")
        
        if self.frequency == RecurrenceFrequency.YEARLY:
            if self.month is None:
                raise ValueError("month is required for YEARLY frequency")
        
        return self


class RecurrenceDTO(BaseModel):
    model_config = ConfigDict(ser_json_exclude_none=True)

    frequency: str
    date_system: str
    calendar_type: Optional[str] = None
    month: Optional[int] = None
    day: int
    duration_days: int


class EventDTO(BaseModel):
    model_config = ConfigDict(ser_json_exclude_none=True)

    id: UUID
    plan_id: Optional[UUID] = None
    accumulator_id: Optional[UUID] = None
    mantra_id: Optional[UUID] = None
    timer_id: Optional[UUID] = None
    group_recitation_collection_id: Optional[UUID] = None
    group_id: UUID
    location_id: Optional[UUID] = None
    location: Optional[LocationDTO] = None
    start_date: datetime
    end_date: datetime
    is_one_day: bool
    featured: bool
    is_recurring: bool = False
    recurrence: Optional[RecurrenceDTO] = None
    occurrence_date: Optional[datetime] = Field(
        None,
        description="For expanded occurrences, the specific occurrence date"
    )
    metadata: EventMetadataResponse
    links: List[EventLinkDTO] = []
    image: Optional[ImageUrlModel] = None
    image_url: Optional[str] = None
    group_name: Optional[str] = None
    group_avatar_url: Optional[str] = None
    participant_count: int = 0
    is_joined: Optional[bool] = Field(
        None,
        description="Whether the authenticated user has joined (null when unauthenticated)",
    )
    created_at: datetime
    created_by: str
    updated_at: Optional[datetime] = None


class EventsResponse(BaseModel):
    events: List[EventDTO]
    total: int
    skip: int
    limit: int


class EventParticipantDTO(BaseModel):
    model_config = ConfigDict(ser_json_exclude_none=True)

    user_id: UUID
    username: Optional[str] = None
    fullname: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: datetime


class EventParticipantsResponse(BaseModel):
    participants: List[EventParticipantDTO]
    skip: int
    limit: int
    total: int


class CreateEventRequest(BaseModel):
    group_id: UUID
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    metadata: List[EventMetadataInput]
    links: List[EventLinkInput] = []
    image_url: Optional[str] = None
    plan_id: Optional[UUID] = None
    accumulator_id: Optional[UUID] = None
    mantra_id: Optional[UUID] = None
    timer_id: Optional[UUID] = None
    group_recitation_collection_id: Optional[UUID] = None
    location_id: Optional[UUID] = None
    recurrence: Optional[RecurrenceInput] = None

    @field_validator("metadata")
    @classmethod
    def validate_metadata_not_empty(cls, value: List[EventMetadataInput]) -> List[EventMetadataInput]:
        if not value:
            raise ValueError("At least one metadata entry is required")
        return _validate_unique_languages(value)

    @model_validator(mode="after")
    
def validate_dates(self) -> "CreateEventRequest":
    # Validation for recurrence (from develop)
    if self.recurrence is None:
        if self.start_date is None or self.end_date is None:
            raise ValueError("start_date and end_date are required when recurrence is not provided")
        _validate_date_range(self.start_date, self.end_date)
        
        # Past date validation (from feature-bug) - only for non-recurring events
        today_utc = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        start_date_utc = self.start_date.astimezone(timezone.utc) if self.start_date.tzinfo else self.start_date.replace(tzinfo=timezone.utc)
        if start_date_utc < today_utc:
            raise ValueError("start_date cannot be in the past")
    
    return self


class UpdateEventRequest(BaseModel):
    group_id: Optional[UUID] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    metadata: Optional[List[EventMetadataInput]] = None
    links: Optional[List[EventLinkInput]] = None
    image_url: Optional[str] = None
    plan_id: Optional[UUID] = None
    accumulator_id: Optional[UUID] = None
    mantra_id: Optional[UUID] = None
    timer_id: Optional[UUID] = None
    group_recitation_collection_id: Optional[UUID] = None
    location_id: Optional[UUID] = None
    recurrence: Optional[RecurrenceInput] = None

    @field_validator("metadata")
    @classmethod
    def validate_metadata_languages(cls, value: Optional[List[EventMetadataInput]]) -> Optional[List[EventMetadataInput]]:
        if value is None:
            return value
        if not value:
            raise ValueError("Metadata list cannot be empty when provided")
        return _validate_unique_languages(value)
