from typing import Dict, List

from pydantic import BaseModel


class SegmentIdRemapRequest(BaseModel):
    old_segment_id: str
    new_segment_id: str


class TextIdRemapRequest(BaseModel):
    old_text_id: str
    new_text_id: str


class IdRemapSkippedEntry(BaseModel):
    table: str
    reason: str
    detail: Dict[str, str]


class IdRemapResult(BaseModel):
    old_id: str
    new_id: str
    updated_counts: Dict[str, int]
    skipped: List[IdRemapSkippedEntry]
