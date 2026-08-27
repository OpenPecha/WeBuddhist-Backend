from pydantic import BaseModel
from uuid import UUID
from typing import List, Optional


class CreateUserRecitationRequest(BaseModel):
    text_id: UUID


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
    text_id: UUID
    display_order: int


class UpdateRecitationOrderRequest(BaseModel):
    recitations: List[RecitationOrderItem]
