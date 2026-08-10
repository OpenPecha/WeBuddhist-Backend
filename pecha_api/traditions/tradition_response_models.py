from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from pecha_api.traditions.tradition_onboarding import list_tradition_path_codes


class SaveUserTraditionRequest(BaseModel):
    tradition_code: str = Field(min_length=1)

    @field_validator("tradition_code")
    @classmethod
    def normalize_tradition_code(cls, value: str) -> str:
        normalized = value.strip()
        if normalized not in list_tradition_path_codes():
            raise ValueError("tradition_code must be one of: pali, chinese, tibetan")
        return normalized


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
