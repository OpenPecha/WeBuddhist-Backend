from typing import List, Optional, Dict, Union
from uuid import UUID
from enum import Enum

from pecha_api.collections.collections_response_models import CollectionModel

from pydantic import BaseModel

from .texts_enums import TextType, PaginationDirection

class CreateTextRequest(BaseModel):
    pecha_text_id:Optional[str] = None
    title: str
    language: Optional[str] = None
    isPublished: bool = False
    group_id: str
    published_by: str
    type: TextType
    categories: Optional[List[str]] = None
    views: Optional[int] = 0
    source_link:Optional[str] = None
    ranking:Optional[int] = None
    license:Optional[str] = None

class UpdateTextRequest(BaseModel):
    title: str
    is_published: Optional[bool] = False

class TextDTO(BaseModel):
    id: str
    pecha_text_id:Optional[str] = None
    title: str
    language: Optional[str] = None
    group_id: str
    type: str
    summary: Optional[str] = ""
    is_published: bool
    created_date: str
    updated_date: str
    published_date: str
    published_by: str
    categories: Optional[List[str]] = None
    views: Optional[int] = 0
    likes: Optional[List[str]] = []
    source_link:Optional[str] = None
    ranking:Optional[int] = None
    license:Optional[str] = None
    
class TextDTOResponse(BaseModel):
    texts: List[TextDTO]
    skip: int
    limit: int
    total: int

# Text TOC Response Models
class Translation(BaseModel):
    text_id: str
    language: str
    content: str

class DetailTextSegment(BaseModel):
    segment_id: str
    segment_number: Optional[int] = None
    content: Optional[str] = None
    translation: Optional[Translation] = None

class DetailSection(BaseModel):
    id: str
    title: str
    section_number: int
    parent_id: Optional[str] = None
    segments: List[DetailTextSegment] = []
    sections: Optional[List["DetailSection"]] = None
    created_date: Optional[str] = None
    updated_date: Optional[str] = None
    published_date: Optional[str] = None

class DetailTableOfContent(BaseModel):
    id: str
    text_id: str
    sections: List[DetailSection]

class DetailTableOfContentResponse(BaseModel):
    text_detail: TextDTO
    content: DetailTableOfContent
    size: int
    pagination_direction: PaginationDirection
    current_segment_position: int
    total_segments: int

class TextSegment(BaseModel):
    segment_id: Optional[str] = None
    pecha_segment_id: Optional[str] = None
    segment_number: int

class Section(BaseModel):
    id: str
    title: Optional[str] = None
    section_number: int
    parent_id: Optional[str] = None
    segments: List[TextSegment] = []
    sections: Optional[List["Section"]] = None
    created_date: Optional[str] = None
    updated_date: Optional[str] = None
    published_date: Optional[str] = None

class TableOfContentType(Enum):
    TEXT = "text"
    SHEET = "sheet"
class TableOfContent(BaseModel):
    id: Optional[str] = None
    type: TableOfContentType
    text_id: str
    sections: List[Section]

class TableOfContentResponse(BaseModel):
    text_detail: TextDTO
    contents: List[TableOfContent]


class TextDetailsRequest(BaseModel):
    content_id: Optional[str] = None
    version_id: Optional[str] = None
    segment_id: Optional[str] = None
    section_id: Optional[str] = None
    size: int = 20
    direction: PaginationDirection = PaginationDirection.NEXT

# Text Version Response Models

class TextVersion(BaseModel):
    id: str
    title: str
    parent_id: Optional[str] = None
    priority: Optional[int] = None
    language: str
    type: str
    group_id: Optional[str] = None 
    table_of_contents: List[str] = []
    is_published: bool
    created_date: str
    updated_date: str
    published_date: str
    published_by: str
    source_link:Optional[str] = None
    ranking:Optional[int] = None
    license:Optional[str] = None

class TextVersionResponse(BaseModel):
    text: Optional[TextDTO] = None
    versions: Optional[List[TextVersion]] = None

# Texts Category Response Models


class TextsCategoryResponse(BaseModel):
    collection: Optional[CollectionModel]
    texts : List[TextDTO]
    total: int
    skip: int
    limit: int

# Texts Info Response Models
class RelatedTexts(BaseModel):
    id: str
    title: str
    count: int

class TextInfos(BaseModel):
    text_id: str
    about_text: str
    translations: int
    related_texts: List[RelatedTexts]
    sheets: int
    web_pages: int
    short_url: str

class TextInfosResponse(BaseModel):
    text_infos: TextInfos

class TextsByPechaTextIdsRequest(BaseModel):
    pecha_text_ids: List[str]
