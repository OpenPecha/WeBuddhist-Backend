from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import date, datetime


class VerseOfDayDTO(BaseModel):
    id: UUID
    verse: str
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


class CreateVerseOfDayRequest(BaseModel):
    verse: str
    image_urls: Optional[List[str]] = None
    verse_id: str
    ref_id: str
    ref_type: str
    group_id: Optional[UUID] = None
    date: date


class UpdateVerseOfDayRequest(BaseModel):
    verse: Optional[str] = None
    image_urls: Optional[List[str]] = None
    verse_id: Optional[str] = None
    ref_id: Optional[str] = None
    ref_type: Optional[str] = None
    group_id: Optional[UUID] = None
    date: Optional[date] = None
