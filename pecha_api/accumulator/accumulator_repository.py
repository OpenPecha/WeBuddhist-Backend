from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from typing import List, Tuple, Optional, Dict
from uuid import UUID
import _datetime
from _datetime import datetime
from fastapi import HTTPException
from starlette import status
from .accumulator_models import Accumulator
from .mala_image_model import MalaImage
from .accumulator_history_model import AccumulatorHistory
from .accumulator_enums import AccumulatorType
from ..mantra.mantra_model import Mantra
from ..mantra.mantra_metadata_model import MantraMetadata


def mantra_exists(db: Session, mantra_id: UUID) -> bool:
    return db.query(Mantra.id).filter(Mantra.id == mantra_id).first() is not None


def get_mantra_mala_image_id(db: Session, mantra_id: UUID) -> Optional[UUID]:
    """Return the mantra's default mala image id, or None if the mantra has
    none set (or no mantra)."""
    return (
        db.query(Mantra.mala_image)
        .filter(Mantra.id == mantra_id)
        .scalar()
    )


def get_mala_image_by_id(db: Session, mala_image_id: UUID) -> Optional[MalaImage]:
    return db.query(MalaImage).filter(MalaImage.id == mala_image_id).first()


def add_accumulator(db: Session, accumulator: Accumulator) -> Accumulator:
    """Stage and flush the accumulator so its id is usable by dependent rows
    (e.g. history). Caller is responsible for the final commit."""
    db.add(accumulator)
    db.flush()
    return accumulator


def commit_accumulator(db: Session, accumulator: Accumulator) -> Accumulator:
    try:
        db.commit()
        db.refresh(accumulator)
        return accumulator
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "BAD_REQUEST", "message": str(e.orig)}
        )


def save_accumulator(db: Session, accumulator: Accumulator) -> Accumulator:
    add_accumulator(db, accumulator)
    return commit_accumulator(db, accumulator)


def get_accumulator_by_id(
    db: Session,
    accumulator_id: UUID,
    include_deleted: bool = False
) -> Optional[Accumulator]:
    query = db.query(Accumulator).filter(Accumulator.id == accumulator_id)
    if not include_deleted:
        query = query.filter(Accumulator.deleted_at.is_(None))
    return query.first()


def update_accumulator(db: Session, accumulator: Accumulator) -> Accumulator:
    try:
        db.commit()
        db.refresh(accumulator)
        return accumulator
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "BAD_REQUEST", "message": str(e.orig)}
        )


def delete_accumulator(db: Session, accumulator: Accumulator) -> None:
    """Soft-delete: mark deleted_at so the accumulator drops out of active
    lists while its history rows are preserved for the user's me/history page."""
    try:
        accumulator.deleted_at = datetime.now(_datetime.timezone.utc)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "BAD_REQUEST", "message": str(e)}
        )


def get_all_accumulators(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = None,
) -> Tuple[List[Accumulator], int]:
    """Public list: only group-defined presets, never users' own accumulators.

    When `search` is provided, results are limited to presets whose mantra
    metadata (mantra text, title, or pronunciation) matches the term
    (case-insensitive substring), across any language.
    """
    query = (
        db.query(Accumulator)
        .filter(
            Accumulator.type == AccumulatorType.PRESET,
            Accumulator.deleted_at.is_(None),
        )
    )

    if search:
        term = f"%{search.strip()}%"
        matching_mantra_ids = (
            db.query(MantraMetadata.mantra_id)
            .filter(
                func.coalesce(MantraMetadata.mantra, "").ilike(term)
                | func.coalesce(MantraMetadata.title, "").ilike(term)
                | func.coalesce(MantraMetadata.pronunciation, "").ilike(term)
            )
        )
        query = query.filter(Accumulator.mantra_id.in_(matching_mantra_ids))

    total = query.count()
    accumulators = query.order_by(Accumulator.created_at.desc()).offset(skip).limit(limit).all()

    return accumulators, total


def get_preset_by_id(db: Session, preset_id: UUID) -> Optional[Accumulator]:
    """Fetch an active preset row (type=PRESET) by id, or None."""
    return (
        db.query(Accumulator)
        .filter(
            Accumulator.id == preset_id,
            Accumulator.type == AccumulatorType.PRESET,
            Accumulator.deleted_at.is_(None),
        )
        .first()
    )


def get_user_accumulator_by_parent(
    db: Session,
    user_id: UUID,
    parent_id: UUID,
) -> Optional[Accumulator]:
    """Fetch the user's active accumulator created from a given preset
    (parent_id), or None. A user has at most one active accumulator per preset."""
    return (
        db.query(Accumulator)
        .filter(
            Accumulator.user_id == user_id,
            Accumulator.parent_id == parent_id,
            Accumulator.deleted_at.is_(None),
        )
        .first()
    )


def get_user_accumulators(
    db: Session,
    user_id: UUID,
    skip: int = 0,
    limit: int = 20
) -> Tuple[List[Accumulator], int]:

    query = (
        db.query(Accumulator)
        .filter(Accumulator.user_id == user_id, Accumulator.deleted_at.is_(None))
    )

    total = query.count()
    accumulators = query.order_by(Accumulator.created_at.desc()).offset(skip).limit(limit).all()

    return accumulators, total


def get_user_total_count(db: Session, user_id: UUID) -> int:
    """Total accumulated count across all of the user's accumulators (all types)."""
    total = (
        db.query(func.sum(AccumulatorHistory.count))
        .filter(AccumulatorHistory.user_id == user_id)
        .scalar()
    )
    return total or 0


def add_history_row(db: Session, accumulator_id: UUID, user_id: UUID, count: int) -> None:
    """Stage a history row recording a positive count delta. Caller commits."""
    db.add(
        AccumulatorHistory(
            accumulator_id=accumulator_id,
            user_id=user_id,
            count=count
        )
    )


def get_accumulator_with_history(
    db: Session,
    user_id: UUID,
    parent_id: UUID,
) -> Optional[Tuple[Accumulator, int, List[AccumulatorHistory]]]:
    """Fetch the user's active accumulator created from a given preset
    (parent_id), along with their total counted and ordered session rows.
    Returns None if the user has no accumulator for that preset."""
    accumulator = get_user_accumulator_by_parent(db, user_id, parent_id)
    if not accumulator:
        return None

    accumulator_id = accumulator.id

    total_counted = (
        db.query(func.sum(AccumulatorHistory.count))
        .filter(
            AccumulatorHistory.accumulator_id == accumulator_id,
            AccumulatorHistory.user_id == user_id
        )
        .scalar()
    ) or 0

    sessions = (
        db.query(AccumulatorHistory)
        .filter(
            AccumulatorHistory.accumulator_id == accumulator_id,
            AccumulatorHistory.user_id == user_id
        )
        .order_by(AccumulatorHistory.created_at.desc())
        .all()
    )

    return accumulator, total_counted, sessions


def get_user_accumulator_history(
    db: Session,
    user_id: UUID,
    skip: int = 0,
    limit: int = 20
) -> Tuple[List[Tuple[Accumulator, int, List[AccumulatorHistory]]], int]:

    accumulator_ids_with_history = (
        db.query(AccumulatorHistory.accumulator_id)
        .filter(AccumulatorHistory.user_id == user_id)
        .distinct()
        .subquery()
    )

    total = db.query(Accumulator).filter(Accumulator.id.in_(accumulator_ids_with_history)).count()

    accumulators = (
        db.query(Accumulator)
        .filter(Accumulator.id.in_(accumulator_ids_with_history))
        .order_by(Accumulator.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    if not accumulators:
        return [], 0

    accumulator_ids = [accumulator.id for accumulator in accumulators]

    totals_query = (
        db.query(
            AccumulatorHistory.accumulator_id,
            func.sum(AccumulatorHistory.count).label('total_count')
        )
        .filter(
            AccumulatorHistory.accumulator_id.in_(accumulator_ids),
            AccumulatorHistory.user_id == user_id
        )
        .group_by(AccumulatorHistory.accumulator_id)
        .all()
    )
    totals_map = {row.accumulator_id: row.total_count or 0 for row in totals_query}

    all_sessions = (
        db.query(AccumulatorHistory)
        .filter(
            AccumulatorHistory.accumulator_id.in_(accumulator_ids),
            AccumulatorHistory.user_id == user_id
        )
        .order_by(AccumulatorHistory.created_at.desc())
        .all()
    )

    sessions_map: Dict[UUID, List[AccumulatorHistory]] = {}
    for session in all_sessions:
        if session.accumulator_id not in sessions_map:
            sessions_map[session.accumulator_id] = []
        sessions_map[session.accumulator_id].append(session)

    result = []
    for accumulator in accumulators:
        total_count = totals_map.get(accumulator.id, 0)
        sessions = sessions_map.get(accumulator.id, [])
        result.append((accumulator, total_count, sessions))

    return result, total
