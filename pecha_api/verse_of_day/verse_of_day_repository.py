from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from datetime import date

from .verse_of_day_model import VerseOfDay


def get_verse_of_day_by_filters(
    db: Session,
    group_id: Optional[UUID] = None,
    filter_date: Optional[date] = None
) -> Optional[VerseOfDay]:

    query = db.query(VerseOfDay)
    
    if group_id is not None:
        query = query.filter(VerseOfDay.group_id == group_id)
    
    if filter_date is not None:
        query = query.filter(VerseOfDay.date == filter_date)
    
    return query.first()


def get_verse_of_day_by_id(db: Session, verse_id: UUID) -> Optional[VerseOfDay]:

    return db.query(VerseOfDay).filter(VerseOfDay.id == verse_id).first()


def get_verse_of_day_today(db: Session, today: date) -> Optional[VerseOfDay]:

    return db.query(VerseOfDay).filter(VerseOfDay.date == today).first()
