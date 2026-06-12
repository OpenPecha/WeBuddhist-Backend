from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from typing import List, Tuple, Optional, Dict
from uuid import UUID
from fastapi import HTTPException
from starlette import status
from .accumulator_models import Accumulator
from .accumulator_history_model import AccumulatorHistory


def save_accumulator(db: Session, accumulator: Accumulator) -> Accumulator:
    try:
        db.add(accumulator)
        db.commit()
        db.refresh(accumulator)
        return accumulator
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "BAD_REQUEST", "message": str(e.orig)}
        )


def get_accumulator_by_id(db: Session, accumulator_id: UUID) -> Optional[Accumulator]:
    return db.query(Accumulator).filter(Accumulator.id == accumulator_id).first()


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
    try:
        db.delete(accumulator)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "BAD_REQUEST", "message": str(e)}
        )


def get_accumulators_by_group(
    db: Session,
    group_id: Optional[UUID] = None,
    skip: int = 0,
    limit: int = 20
) -> Tuple[List[Accumulator], int]:

    query = db.query(Accumulator)
    if group_id:
        query = query.filter(Accumulator.group_id == group_id)

    total = query.count()
    accumulators = query.order_by(Accumulator.created_at.desc()).offset(skip).limit(limit).all()

    return accumulators, total


def get_user_accumulators_by_group(
    db: Session,
    user_id: UUID,
    group_id: Optional[UUID] = None,
    skip: int = 0,
    limit: int = 20
) -> Tuple[List[Accumulator], int]:

    query = db.query(Accumulator).filter(Accumulator.user_id == user_id)
    if group_id:
        query = query.filter(Accumulator.group_id == group_id)

    total = query.count()
    accumulators = query.order_by(Accumulator.created_at.desc()).offset(skip).limit(limit).all()

    return accumulators, total


def record_accumulator_count(
    db: Session,
    accumulator: Accumulator,
    user_id: UUID,
    count: int
) -> Accumulator:
    try:
        accumulator.current_count = (accumulator.current_count or 0) + count
        history = AccumulatorHistory(
            accumulator_id=accumulator.id,
            user_id=user_id,
            count=count
        )
        db.add(history)
        db.commit()
        db.refresh(accumulator)
        return accumulator
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "BAD_REQUEST", "message": str(e.orig)}
        )


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
