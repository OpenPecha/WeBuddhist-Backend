from pydantic import BaseModel, field_validator
from typing import Any, List, Optional
from uuid import UUID


def _stringify_uuid(value: Any) -> Any:
    return str(value) if isinstance(value, UUID) else value


class CreateUserRecitationRequest(BaseModel):
    # str, not UUID: text_id can hold a non-UUID pecha-style text id.
    text_id: str

    @field_validator("text_id", mode="before")
    @classmethod
    def _coerce_text_id(cls, value: Any) -> Any:
        return _stringify_uuid(value)


class UserRecitationDTO(BaseModel):
    title: Optional[str] = None
    # str, not UUID: text_id can hold a non-UUID pecha-style text id.
    text_id: Optional[str] = None
    image_url: Optional[str] = None
    language: Optional[str] = None
    display_order: Optional[int] = None


class UserRecitationsResponse(BaseModel):
    recitations: List[UserRecitationDTO]


class RecitationOrderItem(BaseModel):
    # str, not UUID: text_id can hold a non-UUID pecha-style text id.
    text_id: str
    display_order: int

    @field_validator("text_id", mode="before")
    @classmethod
    def _coerce_text_id(cls, value: Any) -> Any:
        return _stringify_uuid(value)


class UpdateRecitationOrderRequest(BaseModel):
    recitations: List[RecitationOrderItem]
