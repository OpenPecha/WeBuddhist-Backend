from typing import List, Tuple, Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload
from starlette import status

from .event_model import Event
from .event_metadata_model import EventMetadata
from .event_link_model import EventLink


def _persist_metadata_entries(db: Session, event_id: UUID, metadata_entries: List) -> None:
    for entry in metadata_entries:
        db.add(
            EventMetadata(
                event_id=event_id,
                name=entry.name,
                description=entry.description,
                language=entry.language,
            )
        )


def _persist_link_entries(db: Session, event_id: UUID, link_entries: List) -> None:
    for entry in link_entries:
        db.add(
            EventLink(
                event_id=event_id,
                type=entry.type,
                url=entry.url,
                label=entry.label,
                display_order=entry.display_order,
            )
        )


def save_event(db: Session, event: Event, metadata_entries: List, link_entries: Optional[List] = None) -> Event:
    try:
        db.add(event)
        db.flush()
        _persist_metadata_entries(db, event.id, metadata_entries)
        _persist_link_entries(db, event.id, link_entries or [])
        db.commit()
        db.refresh(event)
        return get_event_by_id(db, event.id)
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "BAD_REQUEST", "message": str(e.orig)},
        )


def get_event_by_id(db: Session, event_id: UUID) -> Optional[Event]:
    return (
        db.query(Event)
        .options(
            selectinload(Event.metadata_entries),
            selectinload(Event.links),
            selectinload(Event.location),
        )
        .filter(Event.id == event_id)
        .first()
    )


def update_event(
    db: Session,
    event: Event,
    metadata_entries: Optional[List] = None,
    link_entries: Optional[List] = None,
) -> Event:
    try:
        if metadata_entries is not None:
            db.query(EventMetadata).filter(EventMetadata.event_id == event.id).delete()
            _persist_metadata_entries(db, event.id, metadata_entries)
        if link_entries is not None:
            db.query(EventLink).filter(EventLink.event_id == event.id).delete()
            _persist_link_entries(db, event.id, link_entries)
        db.commit()
        db.refresh(event)
        return get_event_by_id(db, event.id)
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "BAD_REQUEST", "message": str(e.orig)},
        )


def delete_event(db: Session, event: Event) -> None:
    try:
        db.delete(event)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "BAD_REQUEST", "message": str(e)},
        )


def _apply_event_filters(
    query,
    group_id: Optional[UUID] = None,
    plan_id: Optional[UUID] = None,
    accumulator_id: Optional[UUID] = None,
    mantra_id: Optional[UUID] = None,
    timer_id: Optional[UUID] = None,
    group_recitation_collection_id: Optional[UUID] = None,
    from_date: Optional = None,
    to_date: Optional = None,
    restrict_group_ids: Optional[List[UUID]] = None,
):
    if restrict_group_ids is not None:
        query = query.filter(Event.group_id.in_(restrict_group_ids))
    if group_id:
        query = query.filter(Event.group_id == group_id)
    if plan_id:
        query = query.filter(Event.plan_id == plan_id)
    if accumulator_id:
        query = query.filter(Event.accumulator_id == accumulator_id)
    if mantra_id:
        query = query.filter(Event.mantra_id == mantra_id)
    if timer_id:
        query = query.filter(Event.timer_id == timer_id)
    if group_recitation_collection_id:
        query = query.filter(
            Event.group_recitation_collection_id == group_recitation_collection_id
        )
    if from_date is not None:
        query = query.filter(Event.end_date >= from_date)
    if to_date is not None:
        query = query.filter(Event.start_date <= to_date)
    return query


def get_events(
    db: Session,
    group_id: Optional[UUID] = None,
    plan_id: Optional[UUID] = None,
    accumulator_id: Optional[UUID] = None,
    mantra_id: Optional[UUID] = None,
    timer_id: Optional[UUID] = None,
    group_recitation_collection_id: Optional[UUID] = None,
    from_date: Optional = None,
    to_date: Optional = None,
    restrict_group_ids: Optional[List[UUID]] = None,
    skip: int = 0,
    limit: int = 20,
    should_sort_newest_first: bool = False,
) -> Tuple[List[Event], int]:
    if restrict_group_ids is not None and not restrict_group_ids:
        return [], 0

    count_query = _apply_event_filters(
        db.query(func.count(Event.id)),
        group_id=group_id,
        plan_id=plan_id,
        accumulator_id=accumulator_id,
        mantra_id=mantra_id,
        timer_id=timer_id,
        group_recitation_collection_id=group_recitation_collection_id,
        from_date=from_date,
        to_date=to_date,
        restrict_group_ids=restrict_group_ids,
    )
    total = count_query.scalar()

    events_query = _apply_event_filters(
        db.query(Event).options(
            selectinload(Event.metadata_entries),
            selectinload(Event.links),
            selectinload(Event.location),
        ),
        group_id=group_id,
        plan_id=plan_id,
        accumulator_id=accumulator_id,
        mantra_id=mantra_id,
        timer_id=timer_id,
        group_recitation_collection_id=group_recitation_collection_id,
        from_date=from_date,
        to_date=to_date,
        restrict_group_ids=restrict_group_ids,
    )
    order_by = (
        (Event.created_at.desc(), Event.id.desc())
        if should_sort_newest_first
        else (Event.start_date.asc(),)
    )
    events = (
        events_query.order_by(*order_by)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return events, total


def get_featured_events(
    db: Session,
    limit: int = 10,
) -> List[Event]:
    events = (
        db.query(Event)
        .options(
            selectinload(Event.metadata_entries),
            selectinload(Event.links),
            selectinload(Event.location),
        )
        .filter(Event.featured == True)
        .order_by(Event.start_date.desc())
        .limit(limit)
        .all()
    )
    return events


def get_recurring_events(
    db: Session,
    group_id: Optional[UUID] = None,
    plan_id: Optional[UUID] = None,
    accumulator_id: Optional[UUID] = None,
    mantra_id: Optional[UUID] = None,
    timer_id: Optional[UUID] = None,
    group_recitation_collection_id: Optional[UUID] = None,
    restrict_group_ids: Optional[List[UUID]] = None,
) -> List[Event]:
    """Get all recurring event templates matching the filters."""
    query = db.query(Event).options(
        selectinload(Event.metadata_entries),
        selectinload(Event.links),
        selectinload(Event.location),
    ).filter(Event.is_recurring == True)
    
    if restrict_group_ids is not None:
        query = query.filter(Event.group_id.in_(restrict_group_ids))
    if group_id:
        query = query.filter(Event.group_id == group_id)
    if plan_id:
        query = query.filter(Event.plan_id == plan_id)
    if accumulator_id:
        query = query.filter(Event.accumulator_id == accumulator_id)
    if mantra_id:
        query = query.filter(Event.mantra_id == mantra_id)
    if timer_id:
        query = query.filter(Event.timer_id == timer_id)
    if group_recitation_collection_id:
        query = query.filter(
            Event.group_recitation_collection_id == group_recitation_collection_id
        )
    
    return query.all()
