from typing import Optional
from uuid import UUID
from datetime import date

from ..db.database import SessionLocal
from .verse_of_day_repository import get_verse_of_day_by_filters, get_verse_of_day_by_id
from .verse_of_day_response_models import VerseOfDayPublicDTO, VerseOfDayPublicResponse


def get_verse_of_day(
    group_id: Optional[UUID] = None,
    filter_date: Optional[date] = None
) -> VerseOfDayPublicResponse:

    with SessionLocal() as db:
        verse = get_verse_of_day_by_filters(db, group_id=group_id, filter_date=filter_date)
        
        if verse is None:
            return VerseOfDayPublicResponse(verse_of_day=None)
        
        return VerseOfDayPublicResponse(
            verse_of_day=VerseOfDayPublicDTO(
                verse=verse.verse,
                image_urls=verse.image_urls,
                ref_id=verse.ref_id,
                ref_type=verse.ref_type,
                date=verse.date
            )
        )


def get_verse_of_day_by_id_service(verse_id: UUID) -> VerseOfDayPublicResponse:

    with SessionLocal() as db:
        verse = get_verse_of_day_by_id(db, verse_id=verse_id)
        
        if verse is None:
            return VerseOfDayPublicResponse(verse_of_day=None)
        
        return VerseOfDayPublicResponse(
            verse_of_day=VerseOfDayPublicDTO(
                verse=verse.verse,
                image_urls=verse.image_urls,
                ref_id=verse.ref_id,
                ref_type=verse.ref_type,
                date=verse.date
            )
        )
