from typing import Optional, Dict, Union, List
from uuid import UUID
from datetime import date

from ..db.database import SessionLocal
from .verse_of_day_repository import (
    get_verse_of_day_by_filters, 
    get_verse_of_day_by_id, 
    get_verse_of_day_today, 
    create_verse_of_day,
    create_verse_metadata_bulk
)
from .verse_of_day_response_models import (
    VerseOfDayPublicDTO, 
    VerseOfDayPublicResponse, 
    CreateVerseOfDayRequest, 
    VerseOfDayDTO,
    VersesDict
)
from .verse_of_day_model import VerseOfDay


def build_verses_dict(verse_metadata_list) -> VersesDict:
    """Build a dictionary of verses by language from verse_metadata relationship."""
    verses = {}
    for metadata in verse_metadata_list:
        verses[metadata.lang] = metadata.verse
    return verses


def build_public_dto(verse: VerseOfDay, lang: Optional[str] = None) -> VerseOfDayPublicDTO:
    """Build public DTO with optional language filtering."""
    verses_dict = build_verses_dict(verse.verse_metadata) if verse.verse_metadata else {}
    
    if lang and lang in verses_dict:
        return VerseOfDayPublicDTO(
            id=verse.id,
            verse=verses_dict[lang],
            verses=None,
            image_urls=verse.image_urls,
            ref_id=verse.ref_id,
            ref_type=verse.ref_type,
            date=verse.date
        )
    else:
        return VerseOfDayPublicDTO(
            id=verse.id,
            verses=verses_dict if verses_dict else None,
            verse=None,
            image_urls=verse.image_urls,
            ref_id=verse.ref_id,
            ref_type=verse.ref_type,
            date=verse.date
        )


def get_verse_of_day(
    group_id: Optional[UUID] = None,
    filter_date: Optional[date] = None,
    lang: Optional[str] = None
) -> VerseOfDayPublicResponse:

    with SessionLocal() as db:
        verse = get_verse_of_day_by_filters(db, group_id=group_id, filter_date=filter_date)
        
        if verse is None:
            return VerseOfDayPublicResponse(verse_of_day=None)
        
        return VerseOfDayPublicResponse(
            verse_of_day=build_public_dto(verse, lang)
        )


def get_verse_of_day_by_id_service(
    verse_id: UUID,
    lang: Optional[str] = None
) -> VerseOfDayPublicResponse:

    with SessionLocal() as db:
        verse = get_verse_of_day_by_id(db, verse_id=verse_id)
        
        if verse is None:
            return VerseOfDayPublicResponse(verse_of_day=None)
        
        return VerseOfDayPublicResponse(
            verse_of_day=build_public_dto(verse, lang)
        )


def get_verse_of_day_today_service(
    lang: Optional[str] = None
) -> VerseOfDayPublicResponse:

    with SessionLocal() as db:
        today = date.today()
        verse = get_verse_of_day_today(db, today=today)
        
        if verse is None:
            return VerseOfDayPublicResponse(verse_of_day=None)
        
        return VerseOfDayPublicResponse(
            verse_of_day=build_public_dto(verse, lang)
        )


def create_verse_of_day_service(request: CreateVerseOfDayRequest, created_by: str) -> VerseOfDayDTO:

    with SessionLocal() as db:
        verse_of_day = VerseOfDay(
            verse_id=request.verse_id,
            ref_id=request.ref_id,
            ref_type=request.ref_type,
            image_urls=request.image_urls,
            group_id=request.group_id,
            date=request.date,
            created_by=created_by
        )
        
        created = create_verse_of_day(db, verse_of_day)
        
        create_verse_metadata_bulk(db, created.id, request.verses)
        
        return VerseOfDayDTO(
            id=created.id,
            verses=request.verses,
            verse_id=created.verse_id,
            ref_id=created.ref_id,
            ref_type=created.ref_type,
            image_urls=created.image_urls,
            group_id=created.group_id,
            date=created.date
        )
