from typing import Optional
from uuid import UUID
from datetime import date

from ..db.database import SessionLocal
from .verse_of_day_repository import get_verse_of_day_by_filters, get_verse_of_day_by_id, get_verse_of_day_today, create_verse_of_day
from .verse_of_day_response_models import VerseOfDayPublicDTO, VerseOfDayPublicResponse, CreateVerseOfDayRequest, VerseOfDayDTO
from .verse_of_day_model import VerseOfDay


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


def get_verse_of_day_today_service() -> VerseOfDayPublicResponse:

    with SessionLocal() as db:
        today = date.today()
        verse = get_verse_of_day_today(db, today=today)
        
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


def create_verse_of_day_service(request: CreateVerseOfDayRequest, created_by: str) -> VerseOfDayDTO:

    with SessionLocal() as db:
        verse_of_day = VerseOfDay(
            verse=request.verse,
            verse_id=request.verse_id,
            ref_id=request.ref_id,
            ref_type=request.ref_type,
            image_urls=request.image_urls,
            group_id=request.group_id,
            date=request.date,
            created_by=created_by
        )
        
        created = create_verse_of_day(db, verse_of_day)
        
        return VerseOfDayDTO(
            id=created.id,
            verse=created.verse,
            verse_id=created.verse_id,
            ref_id=created.ref_id,
            ref_type=created.ref_type,
            image_urls=created.image_urls,
            group_id=created.group_id,
            date=created.date
        )
