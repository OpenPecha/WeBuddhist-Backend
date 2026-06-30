from datetime import datetime
from typing import List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


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
    def normalize_tradition_code(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("tradition_code must not be empty")
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
