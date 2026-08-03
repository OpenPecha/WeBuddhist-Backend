from typing import Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from .event_model import Event
from .location_model import Location


def get_locations(
    db: Session,
    group_id: UUID,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
) -> Tuple[List[Location], int]:
    query = db.query(Location).filter(Location.group_id == group_id)
    if search and search.strip():
        query = query.filter(Location.name.ilike(f"%{search.strip()}%"))

    total = query.count()
    locations = (
        query.order_by(Location.name.asc()).offset(skip).limit(limit).all()
    )
    return locations, total


def get_location_by_id(
    db: Session, location_id: UUID, group_id: UUID
) -> Optional[Location]:
    return (
        db.query(Location)
        .filter(Location.id == location_id, Location.group_id == group_id)
        .first()
    )


def get_location_without_group_filter(
    db: Session, location_id: UUID
) -> Optional[Location]:
    return db.query(Location).filter(Location.id == location_id).first()


def get_event_count(db: Session, location_id: UUID) -> int:
    return (
        db.query(func.count(Event.id))
        .filter(Event.location_id == location_id)
        .scalar()
        or 0
    )


def get_event_counts(db: Session, location_ids: List[UUID]) -> Dict[UUID, int]:
    if not location_ids:
        return {}
    rows = (
        db.query(Event.location_id, func.count(Event.id))
        .filter(Event.location_id.in_(location_ids))
        .group_by(Event.location_id)
        .all()
    )
    return {row[0]: row[1] for row in rows}


def save_location(db: Session, location: Location) -> Location:
    db.add(location)
    db.commit()
    db.refresh(location)
    return location


def update_location(db: Session, location: Location) -> Location:
    db.commit()
    db.refresh(location)
    return location


def delete_location(db: Session, location: Location) -> None:
    db.delete(location)
    db.commit()
