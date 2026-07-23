from enum import Enum
from typing import List, Dict, Optional
from pydantic import BaseModel, Field, model_serializer
from uuid import UUID


class Segment(BaseModel):
    id: UUID
    content: str


class RecitationDTO(BaseModel):
    title: str
    text_id: UUID
    image_url: Optional[str] = None
    first_segment: Optional[Segment] = None


class RecitationCollectionItemType(str, Enum):
    RECITATION_COLLECTION = "RECITATION_COLLECTION"
    GROUP_RECITATION_COLLECTION = "GROUP_RECITATION_COLLECTION"


class RecitationCollectionDTO(BaseModel):
    type: RecitationCollectionItemType
    name: str
    collection_id: UUID
    group_id: Optional[UUID] = None
    image_url: Optional[str] = None
    item_count: int = 0

    @model_serializer(mode="wrap")
    def _omit_inapplicable_fields(self, serializer) -> dict:
        data = serializer(self)
        if self.type == RecitationCollectionItemType.RECITATION_COLLECTION:
            data.pop("group_id", None)
        return data


class RecitationsResponse(BaseModel):
    recitations: List[RecitationDTO]
    collections: List[RecitationCollectionDTO] = Field(default_factory=list)
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
