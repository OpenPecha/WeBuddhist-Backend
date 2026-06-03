from __future__ import annotations

from typing import List, Optional, Union

from pydantic import BaseModel


class TextDetailRequest(BaseModel):
    offset: int = 0
    limit: int = 30 # default limit is 30

class ContributionModel(BaseModel):
    role: str
    person_id: Optional[str] = None
    person_bdrc_id: Optional[str] = None
    person_name: Optional[dict] = None
    ai_id: Optional[str] = None


class CriticalEditionModel(BaseModel):
    id: str
    type: str
    source: Optional[str] = None
    colophon: Optional[str] = None
    incipit_title: Optional[str] = None
    alt_incipit_titles: Optional[list[str]] = None


class TextDetailResponse(BaseModel):
    id: str
    title: dict
    language: str
    category_id: str
    license: str
    contributions: list[ContributionModel]
    commentaries: list[str]
    translations: list[str]
    edition_details: List[CriticalEditionModel] = []
    bdrc: Optional[str] = None
    wiki: Optional[str] = None
    date: Optional[str] = None
    alt_titles: Optional[list[dict]] = None
    commentary_of: Optional[str] = None
    translation_of: Optional[str] = None
    segments: Optional[SegmentContentResponse] = None


class SegmentationResponseModel(BaseModel):
    id: str
    edition_id: str
    text_id: str


class SegmentLineModel(BaseModel):
    start: int
    end: int


class SegmentSpans(BaseModel):
    id: str
    lines: list[SegmentLineModel]


class SegmentationSegmentResponseModel(BaseModel):
    items: list[SegmentSpans]
    has_more: bool
    offset: int
    limit: int


class EditionContentResponse(BaseModel):
    content: str


class SegmentContentModel(BaseModel):
    segment_number: int
    id: str
    content: str

class SegmentContentResponse(BaseModel):
    contents: list[SegmentContentModel]
    has_more: bool
    offset: int
    limit: int


# ============================================================================
# New Response Models for /{text_id}/details endpoint
# ============================================================================

class SegmentDTO(BaseModel):
    segment_id: str
    segment_number: int
    content: str
    translation: Optional[str] = None


class SectionDTO(BaseModel):
    id: str
    title: str
    section_number: int
    parent_id: Optional[str] = None
    segments: List[SegmentDTO] = []
    sections: List["SectionDTO"] = []
    created_date: Optional[str] = None
    updated_date: Optional[str] = None
    published_date: Optional[str] = None


class ContentDTO(BaseModel):
    id: str
    text_id: str
    sections: List[SectionDTO] = []


class TextDetailDTO(BaseModel):
    id: str
    pecha_text_id: str
    title: str
    language: str
    group_id: str
    type: str
    summary: str
    is_published: bool
    created_date: str
    updated_date: str
    published_date: str
    published_by: str
    categories: List[str] = []
    views: int
    likes: List[str] = []
    source_link: Optional[str] = None
    ranking: Optional[int] = None
    license: Optional[str] = None


class TextDetailWithContentResponse(BaseModel):
    text_detail: TextDetailDTO
    content: ContentDTO
    size: int
    pagination_direction: str
    current_segment_position: int
    total_segments: int

