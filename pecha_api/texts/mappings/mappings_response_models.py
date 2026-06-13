from typing import List, Optional

from pydantic import BaseModel

from pecha_api.texts.segments.segments_enum import SegmentType
from pecha_api.texts.segments.segments_response_models import MappingResponse


class MappingsModel(BaseModel):
    parent_text_id: str
    segments: List[str]


class TextMapping(BaseModel):
    text_id: str
    segment_id: str
    mappings: List[MappingsModel]


class TextMappingRequest(BaseModel):
    text_mappings: List[TextMapping]


class MappingSegmentDTO(BaseModel):
    id: str
    pecha_segment_id: Optional[str] = None
    text_id: str
    type: SegmentType
    mapping: Optional[List[MappingResponse]] = None


class MappingSegmentResponse(BaseModel):
    segments: List[MappingSegmentDTO]
