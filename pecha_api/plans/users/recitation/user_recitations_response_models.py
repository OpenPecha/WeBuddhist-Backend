from pydantic import BaseModel
from uuid import UUID
from typing import List, Optional

class CreateUserRecitationRequest(BaseModel):
    text_id: UUID

class UserRecitationDTO(BaseModel):
    title: str
    text_id: UUID
    image_url: Optional[str] = None
    language: str
    display_order: int

class UserRecitationsResponse(BaseModel):
    recitations: List[UserRecitationDTO]

class RecitationOrderItem(BaseModel):
    text_id: UUID
    display_order: int

class UpdateRecitationOrderRequest(BaseModel):
    recitations: List[RecitationOrderItem]