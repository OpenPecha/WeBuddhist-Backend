from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from uuid import UUID

class Segment(BaseModel):
    id: UUID
    content: str

class RecitationDTO(BaseModel):
    title: str
    text_id: UUID
    image_url: Optional[str] = None
    first_segment: Optional[Segment] = None

class RecitationsResponse(BaseModel):
    recitations: List[RecitationDTO]
    skip: int
    limit: int
    total: int

class RecitationDetailsRequest(BaseModel):
    language: str
    recitation: List[str] = []
    translations: List[str] = []
    transliterations: List[str] = []
    adaptations: List[str] = []

class RecitationSegment(BaseModel):
    recitation: Dict[str, Segment] = Field(default_factory=dict)
    translations: Dict[str, Segment] = Field(default_factory=dict)
    transliterations: Dict[str, Segment] = Field(default_factory=dict)
    adaptations: Dict[str, Segment] = Field(default_factory=dict)

class RecitationDetailsResponse(BaseModel):
    text_id: UUID
    title: str
    segments: List[RecitationSegment]

