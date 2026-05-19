from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import String, cast, desc, asc, or_, exists, select
from sqlalchemy.orm import Session, selectinload

from pecha_api.plans.series.series_model import Series
from pecha_api.plans.series.series_metadata_model import SeriesMetadata
from pecha_api.plans.plans_models import Plan


def get_series_by_id(db: Session, series_id) -> Optional[Series]:
    return (
        db.query(Series)
        .options(
            selectinload(Series.metadata_entries),
            selectinload(Series.plans).selectinload(Plan.items),
        )
        .filter(Series.id == series_id, Series.deleted_at.is_(None))
        .first()
    )


def get_plans_by_ids(db: Session, plan_ids: List[UUID]) -> List[Plan]:
    if not plan_ids:
        return []
    return db.query(Plan).filter(Plan.id.in_(plan_ids)).all()


def _persist_metadata_entries(
    db: Session,
    series_id: UUID,
    metadata_entries: List,
) -> None:
    for entry in metadata_entries:
        db.add(
            SeriesMetadata(
                series_id=series_id,
                title=entry.title,
                description=entry.description,
                language=entry.language,
            )
        )


def save_series_with_plans(
    db: Session,
    series: Series,
    metadata_entries: List,
    plan_ids: Optional[List[UUID]] = None,
) -> Series:
    db.add(series)
    db.flush()
    _persist_metadata_entries(db, series.id, metadata_entries)
    if plan_ids:
        db.query(Plan).filter(Plan.id.in_(plan_ids)).update(
            {Plan.series_id: series.id},
            synchronize_session=False,
        )
    db.commit()
    db.refresh(series)
    return series


def replace_series_metadata(
    db: Session,
    series_id: UUID,
    metadata_entries: List,
) -> None:
    db.query(SeriesMetadata).filter(SeriesMetadata.series_id == series_id).delete(
        synchronize_session=False
    )
    _persist_metadata_entries(db, series_id, metadata_entries)


def update_series_with_plans(
    db: Session,
    series: Series,
    image: Optional[str],
    featured: bool,
    updated_by: Optional[str],
    plan_ids_to_attach: List[UUID],
    plan_ids_to_detach: List[UUID],
    updated_at,
    metadata_entries: Optional[List] = None,
) -> Series:
    series.image = image
    series.featured = featured
    series.updated_at = updated_at
    series.updated_by = updated_by

    if metadata_entries is not None:
        replace_series_metadata(db, series.id, metadata_entries)

    if plan_ids_to_detach:
        db.query(Plan).filter(Plan.id.in_(plan_ids_to_detach)).update(
            {Plan.series_id: None},
            synchronize_session=False,
        )
    if plan_ids_to_attach:
        db.query(Plan).filter(Plan.id.in_(plan_ids_to_attach)).update(
            {Plan.series_id: series.id},
            synchronize_session=False,
        )

    db.commit()
    db.refresh(series)
    return series


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
        filters.append(
            exists(
                select(1).where(
                    SeriesMetadata.series_id == Series.id,
                    or_(
                        SeriesMetadata.title.ilike(f"%{search}%"),
                        SeriesMetadata.description.ilike(f"%{search}%"),
                    ),
                )
            )
        )

    query = db.query(Series).options(selectinload(Series.metadata_entries))
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
