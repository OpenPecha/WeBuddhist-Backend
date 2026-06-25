from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from pecha_api.db.database import SessionLocal
from pecha_api.plans.shared.metadata_utils import (
    format_metadata_response,
    filter_by_language_with_fallback,
)
from pecha_api.plans.plans_enums import PlanStatus
from pecha_api.plans.series.series_model import Series
from pecha_api.plans.groups.groups_repository import get_author_group_ids
from pecha_api.plans.series.series_repository import (
    get_series_by_id,
    get_series_paginated,
    get_enrolled_count_map_by_series_ids,
    get_plans_by_ids,
    save_series_with_plans,
    clone_series_with_plans,
    clone_series_plans_for_language as clone_series_language_plans,
    get_series_for_clone,
    update_series_with_plans,
    reference_start_date_for_series_plans,
    _REFERENCE_START_DATE_UNSET,
    update_series_status,
    update_series_featured,
    soft_delete_series_with_plan_detach,
    get_random_featured_published_series,
    get_series_plan_schedule_by_series_ids,
)
from pecha_api.plans.series.series_response_models import (
    CreateSeriesRequest,
    UpdateSeriesRequest,
    UpdateSeriesStatusRequest,
    SeriesDTO,
    SeriesListItemDTO,
    SeriesMetadataDTO,
    SeriesPlanDTO,
    SeriesListResponse,
    CloneSeriesPlansRequest,
)
from pecha_api.plans.authors.plan_authors_service import (
    validate_cms_author_details,
    get_image_url,
    safe_get_image_url,
)
from pecha_api.plans.groups.group_summary_models import AuthorGroupSummaryDTO
from pecha_api.plans.shared.permissions import (
    is_reviewer,
    is_super_admin,
    require_can_change_status,
    require_can_create_content,
    require_can_edit_content,
    require_can_read_group_content,
)
from pecha_api.plans.tags.tag_helpers import tags_to_summary_dtos
from starlette import status


_SERIES_UPDATE_PERMISSION_ERROR = "You do not have permission to update this series"


def _to_plan_status(status_value) -> PlanStatus:
    if hasattr(status_value, "value"):
        return PlanStatus(status_value.value)
    return PlanStatus(status_value)


def _language_value(language) -> str:
    if hasattr(language, "value"):
        return language.value
    return str(language)


def _optional_metadata_str(value) -> Optional[str]:
    return value if isinstance(value, str) else None


def _optional_uuid(value) -> Optional[UUID]:
    return value if isinstance(value, UUID) else None


def _metadata_to_dtos(
    entries, language: Optional[str] = None, fallback: bool = False
) -> List[SeriesMetadataDTO]:
    if not entries:
        return []
    if fallback:
        entries = filter_by_language_with_fallback(
            entries=list(entries),
            language=language,
            language_of=lambda entry: _language_value(entry.language),
        )
    elif language:
        language_upper = language.upper()
        entries = [
            entry for entry in entries
            if _language_value(entry.language).upper() == language_upper
        ]
    return sorted(
        [
            SeriesMetadataDTO(
                id=entry.id,
                title=entry.title,
                sub_title=_optional_metadata_str(getattr(entry, "sub_title", None)),
                description=entry.description,
                language=_language_value(entry.language),
            )
            for entry in entries
        ],
        key=lambda metadata_dto: metadata_dto.language,
    )


def _metadata_response(entries, language: Optional[str] = None, fallback: bool = False):
    return format_metadata_response(
        _metadata_to_dtos(entries, language=language, fallback=fallback),
        language=language,
    )


def _build_plan_order_pairs(
    plans_by_language: Optional[Dict[str, List[UUID]]],
) -> List[Tuple[UUID, int]]:
    if not plans_by_language:
        return []
    seen_plan_ids: set = set()
    pairs: List[Tuple[UUID, int]] = []
    for plan_ids in plans_by_language.values():
        display_order = 0
        for plan_id in plan_ids or []:
            if plan_id in seen_plan_ids:
                continue
            seen_plan_ids.add(plan_id)
            pairs.append((plan_id, display_order))
            display_order += 1
    return pairs


def _plan_to_dto(plan, group_id: Optional[UUID] = None) -> SeriesPlanDTO:
    total_days = _plan_total_days(plan)
    return SeriesPlanDTO(
        id=plan.id,
        title=plan.title,
        description=plan.description,
        language=plan.language,
        difficulty_level=plan.difficulty_level,
        image=safe_get_image_url(
            plan.image_url, resource_id=plan.id, resource_type="plan"
        ),
        image_key=plan.image_url,
        tags=tags_to_summary_dtos(plan.tag_list),
        status=_to_plan_status(plan.status),
        featured=bool(plan.featured),
        display_order=plan.display_order,
        start_date=plan.start_date,
        total_days=total_days,
        group_id=group_id,
    )


def _plan_total_days(plan) -> int:
    if hasattr(plan, "items"):
        return len(plan.items) if plan.items else 0
    return int(getattr(plan, "total_days", 0) or 0)


def _series_schedule_from_plans(
    plans,
    published_only: bool = False,
    language: Optional[str] = None,
    fallback: bool = False,
) -> Tuple[Optional[datetime], Optional[datetime], int]:
    sorted_plans = _get_sorted_active_plans(
        plans,
        published_only=published_only,
        language=language,
        fallback=fallback,
    )
    if not sorted_plans:
        return None, None, 0

    schedule_plans = _get_sorted_active_plans(
        plans,
        published_only=True,
        language=language,
        fallback=fallback,
    )
    series_total_days = sum(_plan_total_days(plan) for plan in sorted_plans)
    if not schedule_plans:
        return None, None, series_total_days

    first_published = schedule_plans[0]
    last_published = schedule_plans[-1]
    if not first_published.start_date:
        return None, None, series_total_days

    start_date = first_published.start_date
    if not last_published.start_date:
        return start_date, None, series_total_days

    last_plan_days = _plan_total_days(last_published)
    if last_plan_days <= 0:
        end_date = last_published.start_date
    else:
        end_date = last_published.start_date + timedelta(days=last_plan_days - 1)
    return start_date, end_date, series_total_days


def _get_sorted_active_plans(
    plans,
    published_only: bool = False,
    language: Optional[str] = None,
    fallback: bool = False,
) -> List:
    if not plans:
        return []
    active_plans = [plan for plan in plans if plan.deleted_at is None]
    if published_only:
        active_plans = [
            plan for plan in active_plans
            if _to_plan_status(plan.status) == PlanStatus.PUBLISHED
        ]
    if fallback:
        active_plans = filter_by_language_with_fallback(
            entries=active_plans,
            language=language,
            language_of=lambda plan: _language_value(plan.language),
        )
    elif language:
        language_upper = language.upper()
        active_plans = [
            plan for plan in active_plans
            if _language_value(plan.language).upper() == language_upper
        ]
    return sorted(
        active_plans,
        key=lambda plan: (plan.display_order is None, plan.display_order or 0)
    )


def _active_plan_ids(series: Series) -> List[UUID]:
    return [plan.id for plan in (series.plans or []) if plan.deleted_at is None]


def _series_group_context(series: Series) -> Dict[UUID, UUID]:
    return {
        plan.id: plan.group_id
        for plan in (series.plans or [])
        if plan.deleted_at is None and plan.group_id is not None
    }


def _group_summary_for_series(
    db: Session,
    series: Series,
    language: Optional[str] = None,
) -> Optional[AuthorGroupSummaryDTO]:
    if not series.group_id:
        return None
    from pecha_api.plans.groups.groups_service import get_group_summaries_by_ids

    summaries = get_group_summaries_by_ids(
        db=db,
        group_ids=[series.group_id],
        language=language,
    )
    return summaries.get(series.group_id)


def _group_summaries_for_series_rows(
    db: Session,
    series_rows: List[Series],
    language: Optional[str] = None,
) -> Dict[UUID, AuthorGroupSummaryDTO]:
    from pecha_api.plans.groups.groups_service import get_group_summaries_by_ids

    group_ids = list({row.group_id for row in series_rows if row.group_id})
    return get_group_summaries_by_ids(db=db, group_ids=group_ids, language=language)


def _series_detail_dto(
    db: Session,
    series: Series,
    metadata_language: Optional[str] = None,
    **kwargs,
) -> SeriesDTO:
    plan_group_ids = _series_group_context(series=series)
    group = _group_summary_for_series(
        db=db,
        series=series,
        language=metadata_language,
    )
    enrolled_count = get_enrolled_count_map_by_series_ids(
        db=db,
        series_ids=[series.id],
    ).get(series.id, 0)
    return _series_to_dto(
        series,
        group=group,
        plan_group_ids=plan_group_ids,
        metadata_language=metadata_language,
        enrolled_count=enrolled_count,
        **kwargs,
    )


def _series_to_list_item_dto(
    row: Series,
    plan_count: int = 0,
    enrolled_count: int = 0,
    language: Optional[str] = None,
    group: Optional[AuthorGroupSummaryDTO] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    total_days: int = 0,
    fallback: bool = False,
) -> SeriesListItemDTO:
    return SeriesListItemDTO(
        id=row.id,
        metadata=_metadata_response(row.metadata_entries, language=language, fallback=fallback),
        image=get_image_url(image_url=row.image),
        image_key=row.image,
        author_id=row.author_id,
        featured=bool(row.featured),
        status=_to_plan_status(row.status),
        plan_count=plan_count,
        total_days=total_days,
        start_date=start_date,
        end_date=end_date,
        enrolled_count=enrolled_count,
        group=group,
    )


def _series_to_dto(
    row: Series,
    include_plans: bool = False,
    published_only: bool = False,
    plan_language: Optional[str] = None,
    metadata_language: Optional[str] = None,
    group: Optional[AuthorGroupSummaryDTO] = None,
    plan_group_ids: Optional[Dict[UUID, UUID]] = None,
    enrolled_count: int = 0,
) -> SeriesDTO:
    plans_dtos = []
    series_total_days = 0

    if include_plans:
        sorted_plans = _get_sorted_active_plans(
            row.plans,
            published_only=published_only,
            language=plan_language,
            fallback=True,
        )
        for plan in sorted_plans:
            plan_group_id = plan_group_ids.get(plan.id) if plan_group_ids else None
            plan_dto = _plan_to_dto(plan, group_id=plan_group_id)
            plans_dtos.append(plan_dto)
            series_total_days += plan_dto.total_days

    return SeriesDTO(
        id=row.id,
        metadata=_metadata_response(row.metadata_entries, language=metadata_language, fallback=True),
        image=get_image_url(image_url=row.image),
        image_key=row.image,
        author_id=row.author_id,
        group_id=row.group_id,
        parent_series_id=_optional_uuid(getattr(row, "parent_series_id", None)),
        featured=bool(row.featured),
        status=_to_plan_status(row.status),
        plans=plans_dtos,
        total_days=series_total_days,
        enrolled_count=enrolled_count,
        group=group,
    )


def get_filtered_series(
    search: Optional[str],
    skip: int,
    limit: int,
    language: Optional[str] = None,
    group_id: Optional[UUID] = None,
) -> SeriesListResponse:
    with SessionLocal() as db_session:
        rows, total = get_series_paginated(
            db=db_session,
            search=search,
            skip=skip,
            limit=limit,
            include_deleted=False,
            order_by_field=Series.created_at,
            order_desc=True,
            language=language,
            status=PlanStatus.PUBLISHED,
            published_only=True,
            group_ids=[group_id] if group_id is not None else None,
        )
        group_summaries = _group_summaries_for_series_rows(
            db=db_session,
            series_rows=[row for row, _, _ in rows],
            language=language,
        )
        plans_by_series_id = get_series_plan_schedule_by_series_ids(
            db=db_session,
            series_ids=[row.id for row, _, _ in rows],
        )

    series_dtos: List[SeriesListItemDTO] = []
    for row, plan_count, enrolled_count in rows:
        start_date, end_date, total_days = _series_schedule_from_plans(
            plans_by_series_id.get(row.id, []),
            published_only=True,
            language=language,
            fallback=True,
        )
        series_dtos.append(
            _series_to_list_item_dto(
                row,
                plan_count=plan_count,
                enrolled_count=enrolled_count,
                language=language,
                group=group_summaries.get(row.group_id),
                start_date=start_date,
                end_date=end_date,
                total_days=total_days,
            )
        )
    return SeriesListResponse(
        series=series_dtos,
        skip=skip,
        limit=limit,
        total=total,
    )


def get_random_featured_series(
    language: Optional[str] = None,
    limit: int = 10,
) -> SeriesListResponse:
    from pecha_api.plans.response_message import NO_FEATURED_SERIES_FOUND

    with SessionLocal() as db_session:
        rows, total = get_random_featured_published_series(
            db=db_session,
            limit=limit,
            language=language,
        )
        if total == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=NO_FEATURED_SERIES_FOUND,
            )

        group_summaries = _group_summaries_for_series_rows(
            db=db_session,
            series_rows=[row for row, _, _ in rows],
            language=language,
        )
        plans_by_series_id = get_series_plan_schedule_by_series_ids(
            db=db_session,
            series_ids=[row.id for row, _, _ in rows],
        )

    series_dtos: List[SeriesListItemDTO] = []
    for row, plan_count, enrolled_count in rows:
        start_date, end_date, total_days = _series_schedule_from_plans(
            plans_by_series_id.get(row.id, []),
            published_only=True,
            language=language,
        )
        series_dtos.append(
            _series_to_list_item_dto(
                row,
                plan_count=plan_count,
                enrolled_count=enrolled_count,
                language=language,
                group=group_summaries.get(row.group_id),
                start_date=start_date,
                end_date=end_date,
                total_days=total_days,
            )
        )
    if language:
        series_dtos = [dto for dto in series_dtos if dto.metadata is not None]
        if not series_dtos:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=NO_FEATURED_SERIES_FOUND,
            )
    return SeriesListResponse(
        series=series_dtos,
        skip=0,
        limit=limit,
        total=total,
    )


def get_series_detail(series_id: UUID, language: Optional[str] = None) -> SeriesDTO:
    with SessionLocal() as db_session:
        row = get_series_by_id(db=db_session, series_id=series_id)
        if not row or _to_plan_status(row.status) != PlanStatus.PUBLISHED:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Series with id '{series_id}' not found",
            )
        return _series_detail_dto(
            db_session,
            row,
            include_plans=True,
            published_only=True,
            plan_language=language,
            metadata_language=language,
        )

def get_cms_filtered_series(
    token: str,
    search: Optional[str],
    skip: int,
    limit: int,
    language: Optional[str] = None,
    plan_status: Optional[PlanStatus] = None,
    featured: Optional[bool] = None,
    filter_author_id: Optional[UUID] = None,
) -> SeriesListResponse:
    current_author = validate_cms_author_details(token=token)
    group_ids = None
    author_id = filter_author_id if is_super_admin(current_author) or is_reviewer(current_author) else None
    if not is_super_admin(current_author) and not is_reviewer(current_author):
        with SessionLocal() as db_session:
            group_ids = get_author_group_ids(db=db_session, author_id=current_author.id)
            if not group_ids:
                return SeriesListResponse(series=[], skip=skip, limit=limit, total=0)

    with SessionLocal() as db_session:
        rows, total = get_series_paginated(
            db=db_session,
            search=search,
            skip=skip,
            limit=limit,
            include_deleted=False,
            order_by_field=Series.created_at,
            order_desc=True,
            author_id=author_id,
            language=language,
            status=plan_status,
            featured=featured,
            group_ids=group_ids,
        )
        group_summaries = _group_summaries_for_series_rows(
            db=db_session,
            series_rows=[row for row, _, _ in rows],
            language=language,
        )

    series_dtos: List[SeriesListItemDTO] = [
        _series_to_list_item_dto(
            row,
            plan_count=plan_count,
            enrolled_count=enrolled_count,
            language=language,
            group=group_summaries.get(row.group_id),
        )
        for row, plan_count, enrolled_count in rows
    ]
    return SeriesListResponse(
        series=series_dtos,
        skip=skip,
        limit=limit,
        total=total,
    )


def get_cms_series_detail(
    token: str,
    series_id: UUID,
    language: Optional[str] = None,
) -> SeriesDTO:
    current_author = validate_cms_author_details(token=token)

    with SessionLocal() as db_session:
        row = get_series_by_id(db=db_session, series_id=series_id)
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Series with id '{series_id}' not found",
            )
        require_can_read_group_content(db=db_session, group_id=row.group_id, author=current_author)
        return _series_detail_dto(
            db_session,
            row,
            include_plans=True,
            plan_language=language,
            metadata_language=language,
        )

def _validate_plan_ids(
    db,
    plan_ids: List[UUID],
    series_group_id: UUID,
    current_series_id: Optional[UUID] = None,
) -> None:
    if not plan_ids:
        return

    seen_plan_ids = set()
    unique_plan_ids = [
        plan_id for plan_id in plan_ids
        if not (plan_id in seen_plan_ids or seen_plan_ids.add(plan_id))
    ]

    fetched_plans = get_plans_by_ids(db=db, plan_ids=unique_plan_ids)
    fetched_plans_by_id = {plan.id: plan for plan in fetched_plans}

    for plan_id in unique_plan_ids:
        plan = fetched_plans_by_id.get(plan_id)
        if plan is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Plan with id '{plan_id}' does not exist",
            )
        if plan.deleted_at is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Plan with id '{plan_id}' does not exist",
            )
        if plan.series_id is not None and plan.series_id != current_series_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Plan with id '{plan_id}' is already attached to another series",
            )
        # Plans already in this series inherit the series group; skip group check on reorder.
        is_already_in_series = (
            current_series_id is not None and plan.series_id == current_series_id
        )
        if not is_already_in_series and plan.group_id != series_group_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Plan with id '{plan_id}' must belong to the same group as the series",
            )


def _apply_series_field_updates(series, update_series_request: UpdateSeriesRequest) -> None:
    if update_series_request.image_key is not None:
        series.image = update_series_request.image_key
    if update_series_request.featured is not None:
        series.featured = update_series_request.featured


def update_existing_series(
    token: str,
    series_id: UUID,
    update_series_request: UpdateSeriesRequest,
) -> SeriesDTO:
    current_author = validate_cms_author_details(token=token)

    try:
        with SessionLocal() as db_session:
            series = get_series_by_id(db=db_session, series_id=series_id)
            if not series:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Series with id '{series_id}' not found",
                )
            require_can_edit_content(
                db=db_session,
                group_id=series.group_id,
                author=current_author,
                content_status=series.status,
            )

            if update_series_request.plans is not None:
                plan_order_pairs = _build_plan_order_pairs(update_series_request.plans)
                new_plan_ids = [plan_id for plan_id, _ in plan_order_pairs]
                current_attached = {
                    plan.id for plan in (series.plans or []) if plan.deleted_at is None
                }

                if new_plan_ids:
                    _validate_plan_ids(
                        db=db_session,
                        plan_ids=new_plan_ids,
                        series_group_id=series.group_id,
                        current_series_id=series_id,
                    )

                new_set = set(new_plan_ids)
                to_detach = list(current_attached - new_set)
                # Every plan in the request gets its display_order (re)written,
                # including ones already attached, since order may have changed.
                plans_to_attach = plan_order_pairs
                newly_attached = list(new_set - current_attached)
                staying_ids = current_attached & new_set
                reference_start_date = _REFERENCE_START_DATE_UNSET
                if newly_attached and staying_ids:
                    staying_plans = [
                        plan
                        for plan in (series.plans or [])
                        if plan.deleted_at is None and plan.id in staying_ids
                    ]
                    reference_start_date = reference_start_date_for_series_plans(
                        staying_plans
                    )
            else:
                to_detach = []
                plans_to_attach = []
                newly_attached = []
                reference_start_date = _REFERENCE_START_DATE_UNSET

            _apply_series_field_updates(series, update_series_request)

            update_series_with_plans(
                db=db_session,
                series=series,
                image=series.image,
                featured=series.featured,
                updated_by=current_author.email,
                plans_to_attach=plans_to_attach,
                plan_ids_to_detach=to_detach,
                updated_at=datetime.now(timezone.utc),
                metadata_entries=update_series_request.metadata,
                newly_attached_plan_ids=newly_attached or None,
                reference_start_date=reference_start_date,
            )

            refreshed = get_series_by_id(db=db_session, series_id=series_id)

            return _series_detail_dto(db_session, refreshed, include_plans=True)
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database integrity error: {exc.orig}",
        ) from exc


def update_existing_series_status(
    token: str,
    series_id: UUID,
    update_series_status_request: UpdateSeriesStatusRequest,
) -> SeriesDTO:
    current_author = validate_cms_author_details(token=token)

    try:
        with SessionLocal() as db_session:
            series = get_series_by_id(db=db_session, series_id=series_id)
            if not series:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Series with id '{series_id}' not found",
                )
            require_can_change_status(db=db_session, group_id=series.group_id, author=current_author)

            update_series_status(
                db=db_session,
                series=series,
                status=update_series_status_request.status,
                updated_by=current_author.email,
                updated_at=datetime.now(timezone.utc),
            )

            refreshed = get_series_by_id(db=db_session, series_id=series_id)

            return _series_detail_dto(db_session, refreshed, include_plans=True)
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database integrity error: {exc.orig}",
        ) from exc


def update_existing_series_featured(
    token: str,
    series_id: UUID,
) -> None:
    current_author = validate_cms_author_details(token=token)

    try:
        with SessionLocal() as db_session:
            series = get_series_by_id(db=db_session, series_id=series_id)
            if not series:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Series with id '{series_id}' not found",
                )
            require_can_change_status(db=db_session, group_id=series.group_id, author=current_author)

            update_series_featured(
                db=db_session,
                series=series,
                featured=not series.featured,
                updated_by=current_author.email,
                updated_at=datetime.now(timezone.utc),
            )
        return
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database integrity error: {exc.orig}",
        ) from exc


def _clone_existing_series(
    current_author,
    create_series_request: CreateSeriesRequest,
) -> SeriesDTO:
    target_group_id = create_series_request.group_id
    parent_series_id = create_series_request.parent_series_id

    try:
        with SessionLocal() as db_session:
            parent_series = get_series_for_clone(db=db_session, series_id=parent_series_id)
            if not parent_series:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Series with id '{parent_series_id}' not found",
                )
            # Must be allowed to read the source and to create in the destination.
            require_can_read_group_content(
                db=db_session,
                group_id=parent_series.group_id,
                author=current_author,
            )
            require_can_create_content(
                db=db_session,
                group_id=target_group_id,
                author=current_author,
            )

            cloned = clone_series_with_plans(
                db=db_session,
                parent_series=parent_series,
                target_group_id=target_group_id,
                author_id=current_author.id,
                created_by=current_author.email,
                image=create_series_request.image_key
                if create_series_request.image_key is not None
                else parent_series.image,
                featured=bool(create_series_request.featured),
            )

            saved = get_series_by_id(db=db_session, series_id=cloned.id)
            return _series_detail_dto(db_session, saved, include_plans=True)
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database integrity error: {exc.orig}",
        ) from exc


def create_new_series(token: str, create_series_request: CreateSeriesRequest) -> SeriesDTO:
    current_author = validate_cms_author_details(token=token)

    if create_series_request.is_clone:
        return _clone_existing_series(
            current_author=current_author,
            create_series_request=create_series_request,
        )

    new_series = Series(
        image=create_series_request.image_key,
        author_id=current_author.id,
        group_id=create_series_request.group_id,
        featured=create_series_request.featured if create_series_request.featured is not None else False,
        status=PlanStatus.DRAFT,
    )

    plan_order_pairs = _build_plan_order_pairs(create_series_request.plans)
    plan_ids = [plan_id for plan_id, _ in plan_order_pairs]

    try:
        with SessionLocal() as db_session:
            require_can_create_content(
                db=db_session,
                group_id=create_series_request.group_id,
                author=current_author,
            )
            if plan_ids:
                _validate_plan_ids(
                    db=db_session,
                    plan_ids=plan_ids,
                    series_group_id=create_series_request.group_id,
                )

            saved = save_series_with_plans(
                db=db_session,
                series=new_series,
                metadata_entries=create_series_request.metadata,
                plans_to_attach=plan_order_pairs,
            )

            saved = get_series_by_id(db=db_session, series_id=saved.id)

            return _series_detail_dto(db_session, saved, include_plans=bool(plan_ids))
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database integrity error: {exc.orig}",
        ) from exc


def clone_series_plans_for_language(
    token: str,
    series_id: UUID,
    clone_request: CloneSeriesPlansRequest,
) -> SeriesDTO:
    current_author = validate_cms_author_details(token=token)
    source_language = clone_request.source_language.value
    target_language = clone_request.target_language.value

    try:
        with SessionLocal() as db_session:
            series = get_series_by_id(db=db_session, series_id=series_id)
            if not series:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Series with id '{series_id}' not found",
                )
            require_can_edit_content(
                db=db_session,
                group_id=series.group_id,
                author=current_author,
                content_status=series.status,
            )

            active_plans = [
                plan for plan in (series.plans or []) if plan.deleted_at is None
            ]
            source_plans = [
                plan
                for plan in active_plans
                if _language_value(plan.language).upper() == source_language
            ]
            target_plans = [
                plan
                for plan in active_plans
                if _language_value(plan.language).upper() == target_language
            ]

            if not source_plans:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"No plans found in language '{source_language}' for this series",
                )
            if target_plans:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Plans already exist in language '{target_language}' for this series",
                )

            cloned_plans = clone_series_language_plans(
                db=db_session,
                series_id=series_id,
                source_language=source_language,
                target_language=target_language,
                created_by=current_author.email,
            )
            if not cloned_plans:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Could not clone plans for the requested languages",
                )

            refreshed = get_series_by_id(db=db_session, series_id=series_id)
            return _series_detail_dto(db_session, refreshed, include_plans=True)
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database integrity error: {exc.orig}",
        ) from exc


def delete_existing_series(token: str, series_id: UUID) -> None:
    current_author = validate_cms_author_details(token=token)

    try:
        with SessionLocal() as db_session:
            series = get_series_by_id(db=db_session, series_id=series_id)
            if not series:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Series with id '{series_id}' not found",
                )
            require_can_change_status(db=db_session, group_id=series.group_id, author=current_author)

            soft_delete_series_with_plan_detach(
                db=db_session,
                series=series,
                deleted_by=current_author.email,
            )
        return
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database integrity error: {exc.orig}",
        ) from exc