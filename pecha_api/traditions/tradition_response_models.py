from datetime import datetime
from typing import List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from pecha_api.traditions.tradition_onboarding import list_tradition_path_codes


class TraditionChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1)


class TraditionChatRequest(BaseModel):
    messages: List[TraditionChatMessage] = Field(min_length=1)
    language: str = "en"


class SuggestedTradition(BaseModel):
    code: str
    name: str


class TraditionChatResponse(BaseModel):
    model_config = ConfigDict(ser_json_exclude_none=True)

    message: str
    suggested_traditions: List[SuggestedTradition] = Field(default_factory=list)
    follow_up_questions: List[str] = Field(default_factory=list)
    is_complete: bool = False
    selected_tradition_code: Optional[str] = None
    model: str


class SaveUserTraditionRequest(BaseModel):
    tradition_code: str = Field(min_length=1)

    @field_validator("tradition_code")
    @classmethod
    def validate_tradition_code(cls, value: str) -> str:
        normalized = value.strip()
        if normalized not in list_tradition_path_codes():
            raise ValueError("tradition_code must be one of: pali, chinese, tibetan")
        return normalized


class UserTraditionDTO(BaseModel):
    model_config = ConfigDict(ser_json_exclude_none=True)

    id: UUID
    tradition_code: str
    tradition_name: str
    level: int
    parent_code: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class UserTraditionsResponse(BaseModel):
    traditions: List[UserTraditionDTO]


class TraditionListItemDTO(BaseModel):
    code: str
    name: str
    level: int
    parent_code: Optional[str] = None
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
