from pydantic import BaseModel
from typing import List, Optional

from sqlalchemy.orm import strategies
from .segments_models import Mapping

from .segments_enum import SegmentType
from pecha_api.texts.texts_response_models import TextDTO


class CreateSegment(BaseModel):
    pecha_segment_id: Optional[str] = None
    content: str
    pecha_segment_id: Optional[str] = None
    type: SegmentType
    mapping: Optional[List[Mapping]] = []


class CreateSegmentRequest(BaseModel):
    text_id: str
    segments: List[CreateSegment]


class MappingResponse(BaseModel):
    text_id: str
    segments: List[str]

class SegmentDTO(BaseModel):
    id: str
    pecha_segment_id: Optional[str] = None
    text_id: str
    content: str
    type: SegmentType
    mapping: Optional[List[MappingResponse]] = None
    text: Optional[TextDTO] = None

class SegmentUpdate(BaseModel):
    pecha_segment_id: str
    content: str

class SegmentUpdateRequest(BaseModel):
    pecha_text_id: str
    segments: List[SegmentUpdate]
    
class SegmentContentUpdate(BaseModel):
    pecha_segment_id: str
    content: str


class SegmentContentBulkUpdateRequest(BaseModel):
    segments: List[SegmentContentUpdate]

class MappedSegmentDTO(BaseModel):
    segment_id: str
    content: str

class SegmentResponse(BaseModel):
    segments: List[SegmentDTO]

class ParentSegment(BaseModel):
    segment_id: str
    content: str

# segment translation models
class SegmentTranslation(BaseModel):
    segment_id: str
    text_id: str
    title: str
    source: str
    language: str
    content: str

class SegmentRecitation(BaseModel):
    segment_id: str
    text_id: str
    title: str
    source: str
    language: str
    content: str

class SegmentTransliteration(BaseModel):
    segment_id: str
    text_id: str
    title: str
    source: str
    language: str
    content: str

class SegmentAdaptation(BaseModel):
    segment_id: str
    text_id: str
    title: str
    source: str
    language: str
    content: str

class SegmentTranslationsResponse(BaseModel):
    parent_segment: ParentSegment
    translations: List[SegmentTranslation]

# segment commentary models
class SegmentCommentry(BaseModel):
    text_id: str
    title: str
    segments: List[MappedSegmentDTO]
    language: str
    count: int

class SegmentCommentariesResponse(BaseModel):
    parent_segment: ParentSegment
    commentaries: List[SegmentCommentry]

# segment info models

class SegmentInfosRequest(BaseModel):
    text_id: str

class RelatedText(BaseModel):
    commentaries: Optional[int] = 0
    root_text: Optional[int] = 0

class Resources(BaseModel):
    sheets: int

class SegmentInfo(BaseModel):
    segment_id: str
    text_id: str
    translations: Optional[int] = 0
    related_text: RelatedText
    resources: Resources

class SegmentInfoResponse(BaseModel):
    segment_info: SegmentInfo

# segment's root mapping models

class MappedSegmentResponseDTO(BaseModel):
    segment_id: str
    content: str

class SegmentRootMapping(BaseModel):
    text_id: str
    title: str
    language: str
    segments: List[MappedSegmentResponseDTO]

class SegmentRootMappingResponse(BaseModel):
    parent_segment: ParentSegment
    segment_root_mapping: List[SegmentRootMapping]