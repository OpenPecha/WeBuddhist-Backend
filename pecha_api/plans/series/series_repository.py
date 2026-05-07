from typing import List, Optional, Tuple
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import String, cast, desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from pecha_api.plans.series.series_model import Series
from starlette import status


def save_series(db: Session, series: Series) -> Series:
    try:
        db.add(series)
        db.commit()
        db.refresh(series)
        return series
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{exc.orig}",
        ) from exc


def get_series_by_id(db: Session, series_id) -> Optional[Series]:
    return (
        db.query(Series)
        .options(joinedload(Series.plans))
        .filter(Series.id == series_id, Series.deleted_at.is_(None))
        .first()
    )


def get_series_paginated(
    db: Session,
    search: Optional[str],
    skip: int,
    limit: int,
) -> Tuple[List[Series], int]:
    filters = [Series.deleted_at.is_(None)]
    if search:
        filters.append(cast(Series.name, String).ilike(f"%{search}%"))

    query = db.query(Series).filter(*filters)
    total = query.count()
    rows = (
        query.order_by(desc(Series.created_at), Series.id)
        .offset(skip)
        .limit(limit)
        .all()
    )
    return rows, total
