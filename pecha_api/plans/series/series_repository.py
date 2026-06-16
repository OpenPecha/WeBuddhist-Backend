from datetime import datetime, timezone
from typing import Dict, List, Optional, Sequence, Tuple
from uuid import UUID

from sqlalchemy import String, cast, desc, asc, or_, exists, select, func
from sqlalchemy.orm import Session, selectinload

from pecha_api.plans.plans_enums import PlanStatus, SeriesStatus
from pecha_api.plans.series.series_model import Series
from pecha_api.plans.series.series_metadata_model import SeriesMetadata
from pecha_api.plans.plans_models import Plan
from pecha_api.plans.users.plan_users_models import UserSeriesEnrollment


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


def get_enrolled_count_map_by_series_ids(
    db: Session,
    series_ids: Sequence[UUID],
) -> Dict[UUID, int]:
    """Map series_id -> distinct users with an ACTIVE enrollment in the series."""
    if not series_ids:
        return {}
    rows = (
        db.query(
            UserSeriesEnrollment.series_id,
            func.count(func.distinct(UserSeriesEnrollment.user_id)),
        )
        .filter(
            UserSeriesEnrollment.series_id.in_(series_ids),
            UserSeriesEnrollment.status == SeriesStatus.ACTIVE,
        )
        .group_by(UserSeriesEnrollment.series_id)
        .all()
    )
    return {series_id: int(count or 0) for series_id, count in rows}


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
                sub_title=entry.sub_title,
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


def get_series_for_clone(db: Session, series_id) -> Optional[Series]:
    """Load a series with the full plan tree needed to deep-clone it."""
    from pecha_api.plans.items.plan_items_models import PlanItem
    from pecha_api.plans.tasks.plan_tasks_models import PlanTask
    from pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_models import PlanSubTask

    return (
        db.query(Series)
        .options(
            selectinload(Series.metadata_entries),
            selectinload(Series.plans).selectinload(Plan.tag_list),
            selectinload(Series.plans)
            .selectinload(Plan.items)
            .selectinload(PlanItem.audio),
            selectinload(Series.plans)
            .selectinload(Plan.items)
            .selectinload(PlanItem.tasks)
            .selectinload(PlanTask.sub_tasks)
            .selectinload(PlanSubTask.timestamp),
        )
        .filter(Series.id == series_id, Series.deleted_at.is_(None))
        .first()
    )


def _clone_sub_task(db: Session, src_sub, new_task_id: UUID, created_by: str) -> None:
    from pecha_api.plans.tasks.sub_tasks.plan_sub_tasks_models import PlanSubTask
    from pecha_api.plans.audio.sub_task_timestamps_models import SubTaskTimestamp

    new_sub = PlanSubTask(
        task_id=new_task_id,
        audio_url=src_sub.audio_url,
        content_type=src_sub.content_type,
        content=src_sub.content,
        duration=src_sub.duration,
        source_text_id=src_sub.source_text_id,
        pecha_segment_id=src_sub.pecha_segment_id,
        segment_ids=src_sub.segment_ids,
        display_order=src_sub.display_order,
        created_by=created_by,
        updated_by=created_by,
    )
    db.add(new_sub)
    db.flush()

    if src_sub.timestamp is not None:
        db.add(
            SubTaskTimestamp(
                sub_task_id=new_sub.id,
                start_ms=src_sub.timestamp.start_ms,
                end_ms=src_sub.timestamp.end_ms,
                created_by=created_by,
                updated_by=created_by,
            )
        )


def _clone_task(db: Session, src_task, new_item_id: UUID, created_by: str) -> None:
    from pecha_api.plans.tasks.plan_tasks_models import PlanTask

    new_task = PlanTask(
        plan_item_id=new_item_id,
        title=src_task.title,
        display_order=src_task.display_order,
        estimated_time=src_task.estimated_time,
        is_required=src_task.is_required,
        created_by=created_by,
        updated_by=created_by,
    )
    db.add(new_task)
    db.flush()

    for src_sub in src_task.sub_tasks or []:
        if src_sub.deleted_at is None:
            _clone_sub_task(db, src_sub, new_task.id, created_by)


def _clone_item(db: Session, src_item, new_plan_id: UUID, created_by: str) -> None:
    from pecha_api.plans.items.plan_items_models import PlanItem
    from pecha_api.plans.audio.plan_item_audio_models import PlanItemAudio

    new_item = PlanItem(
        plan_id=new_plan_id,
        day_number=src_item.day_number,
        created_by=created_by,
        updated_by=created_by,
    )
    db.add(new_item)
    db.flush()

    if src_item.audio is not None:
        db.add(
            PlanItemAudio(
                plan_item_id=new_item.id,
                audio_key=src_item.audio.audio_key,
                duration_ms=src_item.audio.duration_ms,
                mime_type=src_item.audio.mime_type,
                file_size_bytes=src_item.audio.file_size_bytes,
                created_by=created_by,
                updated_by=created_by,
            )
        )

    for src_task in src_item.tasks or []:
        if src_task.deleted_at is None:
            _clone_task(db, src_task, new_item.id, created_by)


def _clone_plan(
    db: Session,
    src_plan,
    new_series_id: UUID,
    target_group_id: UUID,
    author_id: UUID,
    created_by: str,
) -> None:
    new_plan = Plan(
        title=src_plan.title,
        description=src_plan.description,
        author_id=author_id,
        group_id=target_group_id,
        series_id=new_series_id,
        language=src_plan.language,
        difficulty_level=src_plan.difficulty_level,
        featured=src_plan.featured,
        display_order=src_plan.display_order,
        status=src_plan.status,
        image_url=src_plan.image_url,
        start_date=src_plan.start_date,
        created_by=created_by,
        updated_by=created_by,
    )
    # Re-link to the same (global) tag rows.
    new_plan.tag_list = list(src_plan.tag_list or [])
    db.add(new_plan)
    db.flush()

    for src_item in src_plan.items or []:
        _clone_item(db, src_item, new_plan.id, created_by)


def clone_series_with_plans(
    db: Session,
    parent_series: Series,
    target_group_id: UUID,
    author_id: UUID,
    created_by: str,
    image: Optional[str],
    featured: bool,
) -> Series:
    """Deep-copy a series and its full plan tree into another group.

    The clone keeps every detail of the parent (metadata, plan content, plan
    statuses, tag links) but lives in ``target_group_id``, is authored by
    ``author_id``, starts as a DRAFT series, and records ``parent_series_id``.
    User-specific data (enrollments, completions, recitations, favorites,
    reviews) is intentionally not copied.
    """
    new_series = Series(
        image=image,
        author_id=author_id,
        group_id=target_group_id,
        parent_series_id=parent_series.id,
        featured=featured,
        status=PlanStatus.DRAFT,
        updated_by=created_by,
    )
    db.add(new_series)
    db.flush()

    for entry in parent_series.metadata_entries or []:
        db.add(
            SeriesMetadata(
                series_id=new_series.id,
                title=entry.title,
                sub_title=entry.sub_title,
                description=entry.description,
                language=entry.language,
            )
        )

    for src_plan in parent_series.plans or []:
        if src_plan.deleted_at is None:
            _clone_plan(
                db,
                src_plan,
                new_series.id,
                target_group_id,
                author_id,
                created_by,
            )

    db.commit()
    db.refresh(new_series)
    return new_series


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
    group_ids: Optional[Sequence[UUID]] = None,
) -> Tuple[List[Tuple[Series, int, int]], int]:

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
                        SeriesMetadata.sub_title.ilike(f"%{search}%"),
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
    if group_ids is not None:
        if not group_ids:
            return [], 0
        filters.append(Series.group_id.in_(group_ids))

    plan_count = _series_active_plans_count_subquery(published_only=published_only).label("plan_count")
    query = db.query(Series, plan_count).options(
        selectinload(Series.metadata_entries)
    )
    if filters:
        query = query.filter(*filters)

    total = query.count()

    if order_by_field is None:
        order_by_field = Series.created_at

    if order_desc:
        query = query.order_by(desc(order_by_field), Series.id)
    else:
        query = query.order_by(asc(order_by_field), Series.id)

    page_rows = query.offset(skip).limit(limit).all()
    enrolled_map = get_enrolled_count_map_by_series_ids(
        db=db,
        series_ids=[series.id for series, _ in page_rows],
    )
    rows = [
        (series, int(count or 0), enrolled_map.get(series.id, 0))
        for series, count in page_rows
    ]
    return rows, total


def get_random_featured_published_series(
    db: Session,
    limit: int = 10,
    language: Optional[str] = None,
) -> Tuple[List[Tuple[Series, int, int]], int]:
    plan_count = _series_active_plans_count_subquery(published_only=True).label("plan_count")
    filters = [
        Series.deleted_at.is_(None),
        Series.featured.is_(True),
        Series.status == PlanStatus.PUBLISHED,
    ]
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
    query = (
        db.query(Series, plan_count)
        .options(selectinload(Series.metadata_entries))
        .filter(*filters)
    )
    total = query.count()
    if total == 0:
        return [], 0

    page_rows = query.order_by(func.random()).limit(limit).all()
    enrolled_map = get_enrolled_count_map_by_series_ids(
        db=db,
        series_ids=[series.id for series, _ in page_rows],
    )
    rows = [
        (series, int(count or 0), enrolled_map.get(series.id, 0))
        for series, count in page_rows
    ]
    return rows, total
