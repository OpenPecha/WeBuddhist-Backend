from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from pecha_api.traditions.tradition_constants import normalize_tradition_code


class SaveUserTraditionRequest(BaseModel):
    tradition_code: str = Field(min_length=1)

    @field_validator("tradition_code")
    @classmethod
    def validate_tradition_code(cls, value: str) -> str:
        return normalize_tradition_code(value)


class UserTraditionDTO(BaseModel):
    model_config = ConfigDict(ser_json_exclude_none=True)

    id: UUID
    tradition_code: str
    tradition_name: str
    created_at: datetime
    updated_at: Optional[datetime] = None


class UserTraditionsResponse(BaseModel):
    traditions: List[UserTraditionDTO]


class TraditionListItemDTO(BaseModel):
    code: str
    name: str
    regions: List[str] = Field(default_factory=list)


class TraditionListResponse(BaseModel):
    traditions: List[TraditionListItemDTO]


class TraditionOnboardingPathDTO(BaseModel):
    title: str
    description: str


class TraditionOnboardingPathsDTO(BaseModel):
    pali: TraditionOnboardingPathDTO
    chinese: TraditionOnboardingPathDTO
    tibetan: TraditionOnboardingPathDTO


class TraditionOnboardingResponse(BaseModel):
    title: str
    subtitle: str
    option_intro: str
    paths: TraditionOnboardingPathsDTO
    footer: str


class TraditionMetadataInput(BaseModel):
    language: str = Field(min_length=2, max_length=8)
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    other_names: Optional[List[str]] = None

    @field_validator("language")
    @classmethod
    def normalize_language(cls, value: str) -> str:
        return value.strip().upper()


class CreateTraditionRequest(BaseModel):
    code: str = Field(min_length=2, max_length=64)
    regions: Optional[List[str]] = None
    parent_id: Optional[UUID] = None
    metadata: List[TraditionMetadataInput] = Field(min_length=1)

    @field_validator("code")
    @classmethod
    def validate_code(cls, value: str) -> str:
        return normalize_tradition_code(value)


class UpdateTraditionRequest(BaseModel):
    code: Optional[str] = Field(default=None, min_length=2, max_length=64)
    regions: Optional[List[str]] = None
    parent_id: Optional[UUID] = None
    metadata: Optional[List[TraditionMetadataInput]] = None

    @field_validator("code")
    @classmethod
    def validate_code(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return normalize_tradition_code(value)


class TraditionMetadataDTO(BaseModel):
    id: UUID
    language: str
    name: str
    description: Optional[str] = None
    other_names: Optional[List[str]] = None


class TraditionCMSDTO(BaseModel):
    id: UUID
    code: str
    regions: List[str] = Field(default_factory=list)
    parent_id: Optional[UUID] = None
    name: str
    description: Optional[str] = None
    metadata: List[TraditionMetadataDTO] = Field(default_factory=list)


class TraditionsCMSListResponse(BaseModel):
    traditions: List[TraditionCMSDTO]
    skip: int
    limit: int
    total: int
