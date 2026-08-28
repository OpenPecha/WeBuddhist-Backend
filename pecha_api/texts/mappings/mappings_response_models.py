from typing import List
from pydantic import BaseModel


class MappingsModel(BaseModel):
    parent_text_id: str
    segments: List[str]


class TextMapping(BaseModel):
    text_id: str
    segment_id: str
    mappings: List[MappingsModel]


class TextMappingRequest(BaseModel):
    text_mappings: List[TextMapping]
