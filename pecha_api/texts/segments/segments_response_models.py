from pydantic import BaseModel
from typing import List, Optional

class ParentSegment(BaseModel):
    segment_id: str
    content: str

class V2RelatedSegmentItem(BaseModel):
    id: str
    content: Optional[str] = None


class V2SegmentTextGroup(BaseModel):
    text_id: str
    title: str
    language: Optional[str] = None
    segments: List[V2RelatedSegmentItem]


class V2SegmentTranslationsResponse(BaseModel):
    parent_segment: ParentSegment
    translations: List[V2SegmentTextGroup]
    skip: int
    limit: int
    has_more: bool = False

class V2SegmentRootTextResponse(BaseModel):
    parent_segment: ParentSegment
    root_text: List[V2SegmentTextGroup]
    skip: int
    limit: int
    has_more: bool = False

class V2SegmentCommentariesResponse(BaseModel):
    parent_segment: ParentSegment
    commentaries: List[V2SegmentTextGroup]
    skip: int
    limit: int
    has_more: bool = False


class V2SegmentTextDetail(BaseModel):
    text_id: str
    title: str
    language: Optional[str] = None


class V2SegmentResponse(BaseModel):
    segment_id: str
    content: str
    text: Optional[V2SegmentTextDetail] = None
