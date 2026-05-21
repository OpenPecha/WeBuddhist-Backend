from __future__ import annotations

from typing import List, Optional

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
    text_id: str
    type: str
    source: Optional[str] = None
    colophon: Optional[str] = None
    incipit_title: Optional[str] = None
    alt_incipit_titles: Optional[list[str]] = None
    bdrc: Optional[str] = None
    wiki: Optional[str] = None


class TextDetailResponse(BaseModel):
    id: str
    title: dict
    language: str
    category_id: str
    license: str
    contributions: list[ContributionModel]
    commentaries: list[str]
    translations: list[str]
    editions: list[str]
    edition_details: List[CriticalEditionModel] = []
    bdrc: Optional[str] = None
    wiki: Optional[str] = None
    date: Optional[str] = None
    alt_titles: Optional[list[dict]] = None
    commentary_of: Optional[str] = None
    translation_of: Optional[str] = None


class SegmentationResponseModel(BaseModel):
    id: str
    edition_id: str
    text_id: str


class SegmentLineModel(BaseModel):
    start: int
    end: int


class segmentSpans(BaseModel):
    id: str
    lines: list[SegmentLineModel]


class SegmentationSegmentResponseModel(BaseModel):
    items: list[segmentSpans]
    has_more: bool
    offset: int
    limit: int


class EditionContentResponse(BaseModel):
    content: str


class SegmentContentModel(BaseModel):
    id: str
    content: str
