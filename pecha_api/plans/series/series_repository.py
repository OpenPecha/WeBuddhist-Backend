from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import String, cast, desc, asc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from pecha_api.plans.series.series_model import Series
from pecha_api.plans.plans_models import Plan


def save_series(db: Session, series: Series) -> Series:
    db.add(series)
    db.commit()
    db.refresh(series)
    return series


def get_series_by_id(db: Session, series_id) -> Optional[Series]:
    return (
        db.query(Series)
        .options(
            selectinload(Series.plans).selectinload(Plan.items)
        )
        .filter(Series.id == series_id, Series.deleted_at.is_(None))
        .first()
    )


def get_series_paginated(
    db: Session,
    search: Optional[str],
    skip: int,
    limit: int,
    include_deleted: bool = False,
    order_by_field=None,
    order_desc: bool = True,
) -> Tuple[List[Series], int]:

    filters = []
    if not include_deleted:
        filters.append(Series.deleted_at.is_(None))
    if search:
        filters.append(cast(Series.name, String).ilike(f"%{search}%"))

    query = db.query(Series)
    if filters:
        query = query.filter(*filters)
    
    total = query.count()
    
    if order_by_field is None:
        order_by_field = Series.created_at
    
    if order_desc:
        query = query.order_by(desc(order_by_field), Series.id)
    else:
        query = query.order_by(asc(order_by_field), Series.id)
    
    rows = query.offset(skip).limit(limit).all()
    return rows, total
