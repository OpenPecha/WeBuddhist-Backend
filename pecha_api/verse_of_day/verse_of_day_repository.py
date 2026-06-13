from sqlalchemy.orm import Session, joinedload
from typing import Optional, List, Dict, Union
from uuid import UUID
from datetime import date

from .verse_of_day_model import VerseOfDay
from .verse_metadata_model import VerseMetadata
from pecha_api.plans.groups.groups_models import AuthorGroupMetadata


def get_verse_of_day_by_filters(
    db: Session,
    group_id: Optional[UUID] = None,
    filter_date: Optional[date] = None
) -> Optional[VerseOfDay]:

    query = db.query(VerseOfDay).options(joinedload(VerseOfDay.verse_metadata))
    
    if group_id is not None:
        query = query.filter(VerseOfDay.group_id == group_id)
    
    if filter_date is not None:
        query = query.filter(VerseOfDay.date == filter_date)
    
    return query.first()


def get_verse_of_day_by_id(db: Session, verse_id: UUID) -> Optional[VerseOfDay]:

    return db.query(VerseOfDay).options(
        joinedload(VerseOfDay.verse_metadata)
    ).filter(VerseOfDay.id == verse_id).first()


def get_verse_of_day_today(db: Session, today: date) -> Optional[VerseOfDay]:

    return db.query(VerseOfDay).options(
        joinedload(VerseOfDay.verse_metadata)
    ).filter(VerseOfDay.date == today).first()


def create_verse_of_day(db: Session, verse_of_day: VerseOfDay) -> VerseOfDay:

    db.add(verse_of_day)
    db.commit()
    db.refresh(verse_of_day)
    return verse_of_day


def create_verse_metadata(
    db: Session, 
    verse_of_day_id: UUID, 
    lang: str, 
    verse: Union[str, List[str]]
) -> VerseMetadata:
    metadata = VerseMetadata(
        verse_of_day_id=verse_of_day_id,
        lang=lang,
        verse=verse
    )
    db.add(metadata)
    db.commit()
    db.refresh(metadata)
    return metadata


def create_verse_metadata_bulk(
    db: Session,
    verse_of_day_id: UUID,
    verses: Dict[str, Union[str, List[str]]]
) -> List[VerseMetadata]:
    metadata_list = []
    for lang, verse in verses.items():
        metadata = VerseMetadata(
            verse_of_day_id=verse_of_day_id,
            lang=lang,
            verse=verse
        )
        db.add(metadata)
        metadata_list.append(metadata)
    
    db.commit()
    for m in metadata_list:
        db.refresh(m)
    return metadata_list


def get_verse_metadata_by_verse_of_day_id(
    db: Session, 
    verse_of_day_id: UUID
) -> List[VerseMetadata]:
    return db.query(VerseMetadata).filter(
        VerseMetadata.verse_of_day_id == verse_of_day_id
    ).all()


def get_verse_metadata_by_lang(
    db: Session,
    verse_of_day_id: UUID,
    lang: str
) -> Optional[VerseMetadata]:
    return db.query(VerseMetadata).filter(
        VerseMetadata.verse_of_day_id == verse_of_day_id,
        VerseMetadata.lang == lang
    ).first()


def get_group_metadata_by_group_id(
    db: Session,
    group_id: UUID
) -> List[AuthorGroupMetadata]:
    return db.query(AuthorGroupMetadata).filter(
        AuthorGroupMetadata.group_id == group_id
    ).all()
