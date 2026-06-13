from pydantic import BaseModel
from typing import Optional, List, Dict, Union
from uuid import UUID
from datetime import date, datetime


# Type alias for verse content (can be string or array of strings)
VerseContent = Union[str, List[str]]

# Type alias for verses dictionary by language
VersesDict = Dict[str, VerseContent]


class GroupInfoDTO(BaseModel):
    """DTO for group metadata information."""
    id: UUID
    title: str
    sub_title: Optional[str] = None
    description: Optional[str] = None
    language: str

    class Config:
        from_attributes = True


class VerseMetadataDTO(BaseModel):
    """DTO for individual verse metadata entry."""
    lang: str
    verse: VerseContent

    class Config:
        from_attributes = True


class VerseOfDayDTO(BaseModel):
    """Full DTO with all languages."""
    id: UUID
    verses: Optional[VersesDict] = None
    image_urls: Optional[List[str]] = None
    verse_id: str
    ref_id: str
    ref_type: str
    group_id: Optional[UUID] = None
    date: date

    class Config:
        from_attributes = True


class VerseOfDayResponse(BaseModel):
    verse_of_day: VerseOfDayDTO


class VerseOfDayPublicDTO(BaseModel):
    """Public DTO - returns all languages as verses dict, or single verse if lang filtered."""
    id: UUID
    verses: Optional[VersesDict] = None
    verse: Optional[VerseContent] = None
    image_urls: Optional[List[str]] = None
    ref_id: str
    ref_type: str
    date: date
    group_info: Optional[List[GroupInfoDTO]] = None

    class Config:
        from_attributes = True


class VerseOfDayPublicResponse(BaseModel):
    verse_of_day: Optional[VerseOfDayPublicDTO] = None


class CreateVerseOfDayRequest(BaseModel):
    """Request to create verse of day with multilingual verses."""
    verses: VersesDict
    image_urls: Optional[List[str]] = None
    verse_id: str
    ref_id: str
    ref_type: str
    group_id: Optional[UUID] = None
    date: date


class UpdateVerseOfDayRequest(BaseModel):
    verses: Optional[VersesDict] = None
    image_urls: Optional[List[str]] = None
    verse_id: Optional[str] = None
    ref_id: Optional[str] = None
    ref_type: Optional[str] = None
    group_id: Optional[UUID] = None
    date: Optional[date] = None
