from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

MAX_LATITUDE = Decimal("90")
MAX_LONGITUDE = Decimal("180")


def _validate_name(value: str) -> str:
    trimmed = value.strip()
    if not trimmed:
        raise ValueError("name must be a non-empty string")
    return trimmed


def _validate_latitude(value: Optional[Decimal]) -> Optional[Decimal]:
    if value is not None and not -MAX_LATITUDE <= value <= MAX_LATITUDE:
        raise ValueError("latitude must be between -90 and 90")
    return value


def _validate_longitude(value: Optional[Decimal]) -> Optional[Decimal]:
    if value is not None and not -MAX_LONGITUDE <= value <= MAX_LONGITUDE:
        raise ValueError("longitude must be between -180 and 180")
    return value


def _validate_coordinates_paired(
    latitude: Optional[Decimal], longitude: Optional[Decimal]
) -> None:
    if (latitude is None) != (longitude is None):
        raise ValueError("latitude and longitude must be provided together")


class LocationDTO(BaseModel):
    model_config = ConfigDict(ser_json_exclude_none=True)

    id: UUID
    group_id: UUID
    name: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class LocationDetailDTO(LocationDTO):
    event_count: int = 0


class LocationsResponse(BaseModel):
    locations: List[LocationDetailDTO]
    skip: int
    limit: int
    total: int


class CreateLocationRequest(BaseModel):
    name: str = Field(max_length=255)
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return _validate_name(value)

    @field_validator("latitude")
    @classmethod
    def validate_latitude(cls, value: Optional[Decimal]) -> Optional[Decimal]:
        return _validate_latitude(value)

    @field_validator("longitude")
    @classmethod
    def validate_longitude(cls, value: Optional[Decimal]) -> Optional[Decimal]:
        return _validate_longitude(value)

    @model_validator(mode="after")
    def validate_coordinates(self) -> "CreateLocationRequest":
        _validate_coordinates_paired(self.latitude, self.longitude)
        return self


class UpdateLocationRequest(BaseModel):
    name: Optional[str] = Field(default=None, max_length=255)
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: Optional[str]) -> str:
        if value is None:
            raise ValueError("name cannot be null")
        return _validate_name(value)

    @field_validator("latitude")
    @classmethod
    def validate_latitude(cls, value: Optional[Decimal]) -> Optional[Decimal]:
        return _validate_latitude(value)

    @field_validator("longitude")
    @classmethod
    def validate_longitude(cls, value: Optional[Decimal]) -> Optional[Decimal]:
        return _validate_longitude(value)

    @model_validator(mode="after")
    def validate_coordinates(self) -> "UpdateLocationRequest":
        latitude_set = "latitude" in self.model_fields_set
        longitude_set = "longitude" in self.model_fields_set
        if latitude_set != longitude_set:
            raise ValueError("latitude and longitude must be provided together")
        if latitude_set:
            _validate_coordinates_paired(self.latitude, self.longitude)
        return self
