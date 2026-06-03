from datetime import datetime, timezone
from typing import Dict, List, Optional, Sequence, Tuple
from uuid import UUID

from sqlalchemy import String, cast, desc, asc, or_, exists, select, func
from sqlalchemy.orm import Session, selectinload

from pecha_api.plans.plans_enums import PlanStatus
from pecha_api.plans.series.series_model import Series
from pecha_api.plans.series.series_metadata_model import SeriesMetadata
from pecha_api.plans.plans_models import Plan
from pecha_api.plans.groups.groups_models import author_group_series


def _series_active_plans_count_subquery(published_only: bool = False):
    conditions = [Plan.series_id == Series.id, Plan.deleted_at.is_(None)]
    if published_only:
        conditions.append(Plan.status == PlanStatus.PUBLISHED)
    return (
        select(func.count(Plan.id))
        .where(*conditions)
        .correlate(Series)
        .scalar_subquery()
    )


def get_series_by_id(db: Session, series_id) -> Optional[Series]:
    return (
        db.query(Series)
        .options(
            selectinload(Series.metadata_entries),
            selectinload(Series.plans).selectinload(Plan.items),
            selectinload(Series.plans).selectinload(Plan.tag_list),
        )
        .filter(Series.id == series_id, Series.deleted_at.is_(None))
        .first()
    )


def get_series_by_ids(db: Session, series_ids: List[UUID]) -> List[Series]:
    if not series_ids:
        return []
    return (
        db.query(Series)
        .options(selectinload(Series.metadata_entries))
        .filter(Series.id.in_(series_ids), Series.deleted_at.is_(None))
        .all()
    )


def get_active_plan_count_map_by_series_ids(
    db: Session,
    series_ids: Sequence[UUID],
    published_only: bool = False,
) -> Dict[UUID, int]:
    if not series_ids:
        return {}
    conditions = [
        Plan.series_id.in_(series_ids),
        Plan.deleted_at.is_(None),
    ]
    if published_only:
        conditions.append(Plan.status == PlanStatus.PUBLISHED)
    rows = (
        db.query(Plan.series_id, func.count(Plan.id))
        .filter(*conditions)
        .group_by(Plan.series_id)
        .all()
    )
    return {series_id: int(count or 0) for series_id, count in rows}


def get_series_with_plans_by_ids(db: Session, series_ids: List[UUID]) -> List[Series]:
    if not series_ids:
        return []
    return (
        db.query(Series)
        .options(
            selectinload(Series.plans).selectinload(Plan.items),
            selectinload(Series.plans).selectinload(Plan.tag_list),
        )
        .filter(Series.id.in_(series_ids), Series.deleted_at.is_(None))
        .all()
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
    plans_to_attach: Optional[List[Tuple[UUID, int]]] = None,
) -> Series:
    db.add(series)
    db.flush()
    _persist_metadata_entries(db, series.id, metadata_entries)
    if plans_to_attach:
        for plan_id, display_order in plans_to_attach:
            db.query(Plan).filter(Plan.id == plan_id).update(
                {
                    Plan.series_id: series.id,
                    Plan.display_order: display_order,
                },
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
    plans_to_attach: List[Tuple[UUID, int]],
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
            {
                Plan.series_id: None,
                Plan.display_order: None,
            },
            synchronize_session=False,
        )
    if plans_to_attach:
        for plan_id, display_order in plans_to_attach:
            db.query(Plan).filter(Plan.id == plan_id).update(
                {
                    Plan.series_id: series.id,
                    Plan.display_order: display_order,
                },
                synchronize_session=False,
            )

    db.commit()
    db.refresh(series)
    return series


def update_series_status(
    db: Session,
    series: Series,
    status,
    updated_by: Optional[str],
    updated_at,
) -> Series:
    series.status = status
    series.updated_at = updated_at
    series.updated_by = updated_by

    db.commit()
    db.refresh(series)
    return series


def update_series_featured(
    db: Session,
    series: Series,
    featured: bool,
    updated_by: Optional[str],
    updated_at,
) -> Series:
    series.featured = featured
    series.updated_at = updated_at
    series.updated_by = updated_by

    db.commit()
    db.refresh(series)
    return series


def soft_delete_series_with_plan_detach(
    db: Session,
    series: Series,
    deleted_by: Optional[str],
) -> None:
    db.query(Plan).filter(Plan.series_id == series.id).update(
        {
            Plan.series_id: None,
            Plan.display_order: None,
        },
        synchronize_session=False,
    )
    series.deleted_at = datetime.now(timezone.utc)
    series.deleted_by = deleted_by
    db.commit()


def get_series_paginated(
    db: Session,
    search: Optional[str],
    skip: int,
    limit: int,
    include_deleted: bool = False,
    order_by_field=None,
    order_desc: bool = True,
    author_id: Optional[UUID] = None,
    language: Optional[str] = None,
    status: Optional[PlanStatus] = None,
    featured: Optional[bool] = None,
    published_only: bool = False,
    group_id: Optional[UUID] = None,
) -> Tuple[List[Tuple[Series, int]], int]:

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
    if author_id is not None:
        filters.append(Series.author_id == author_id)
    if status is not None:
        filters.append(Series.status == status)
    if featured is not None:
        filters.append(Series.featured == featured)
    if language:
        language_upper = language.upper()
        filters.append(
            exists(
                select(1).where(
                    SeriesMetadata.series_id == Series.id,
                    SeriesMetadata.language == language_upper,
                )
            )
        )
    if group_id:
        filters.append(
            exists(
                select(1).where(
                    author_group_series.c.group_id == group_id,
                    author_group_series.c.series_id == Series.id,
                )
            )
        )

    plan_count = _series_active_plans_count_subquery(published_only=published_only).label("plan_count")
    query = db.query(Series, plan_count).options(selectinload(Series.metadata_entries))
    if filters:
        query = query.filter(*filters)

    total = query.count()

    if order_by_field is None:
        order_by_field = Series.created_at

    if order_desc:
        query = query.order_by(desc(order_by_field), Series.id)
    else:
        query = query.order_by(asc(order_by_field), Series.id)

    rows = [
        (series, int(count or 0))
        for series, count in query.offset(skip).limit(limit).all()
    ]
    return rows, total
