from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from pecha_api.config import get
from pecha_api.db.database import SessionLocal
from pecha_api.plans.plans_enums import PlanStatus
from pecha_api.plans.series.series_model import Series
from pecha_api.plans.series.series_repository import (
    get_series_by_id,
    get_series_paginated,
    get_plans_by_ids,
    save_series_with_plans,
    update_series_with_plans,
    update_series_status,
    update_series_featured,
    soft_delete_series_with_plan_detach,
)
from pecha_api.plans.series.series_response_models import (
    CreateSeriesRequest,
    UpdateSeriesRequest,
    UpdateSeriesStatusRequest,
    SeriesDTO,
    SeriesMetadataDTO,
    SeriesPlanDTO,
    SeriesListResponse,
)
from pecha_api.plans.authors.plan_authors_service import validate_and_extract_author_details
from pecha_api.plans.tags.tag_helpers import tags_to_summary_dtos
from pecha_api.uploads.S3_utils import generate_presigned_access_url
from starlette import status


def _generate_image_url(image_key: Optional[str]) -> Optional[str]:
    if not image_key:
        return None
    return generate_presigned_access_url(
        bucket_name=get("AWS_BUCKET_NAME"),
        s3_key=image_key,
    )


def _to_plan_status(status_value) -> PlanStatus:
    if hasattr(status_value, "value"):
        return PlanStatus(status_value.value)
    return PlanStatus(status_value)


def _language_value(language) -> str:
    if hasattr(language, "value"):
        return language.value
    return str(language)


def _metadata_to_dtos(entries) -> List[SeriesMetadataDTO]:
    if not entries:
        return []
    return sorted(
        [
            SeriesMetadataDTO(
                id=entry.id,
                title=entry.title,
                description=entry.description,
                language=_language_value(entry.language),
            )
            for entry in entries
        ],
        key=lambda item: item.language,
    )


def _build_plan_order_pairs(
    plans_by_language: Optional[Dict[str, List[UUID]]],
) -> List[Tuple[UUID, int]]:
    if not plans_by_language:
        return []
    seen: set = set()
    pairs: List[Tuple[UUID, int]] = []
    for ids in plans_by_language.values():
        order = 0
        for pid in ids or []:
            if pid in seen:
                continue
            seen.add(pid)
            pairs.append((pid, order))
            order += 1
    return pairs


def _plan_to_dto(plan) -> SeriesPlanDTO:
    total_days = len(plan.items) if hasattr(plan, 'items') and plan.items else 0
    return SeriesPlanDTO(
        id=plan.id,
        title=plan.title,
        description=plan.description,
        language=plan.language,
        difficulty_level=plan.difficulty_level,
        image_url=_generate_image_url(plan.image_url),
        image_key=plan.image_url,
        tags=tags_to_summary_dtos(plan.tag_list),
        status=_to_plan_status(plan.status),
        featured=bool(plan.featured),
        display_order=plan.display_order,
        start_date=plan.start_date,
        total_days=total_days,
    )


def _get_sorted_active_plans(plans) -> List:
    if not plans:
        return []
    active_plans = [p for p in plans if p.deleted_at is None]
    return sorted(
        active_plans,
        key=lambda p: (p.display_order is None, p.display_order or 0)
    )


def _series_to_dto(row: Series, include_plans: bool = False) -> SeriesDTO:
    plans_dtos = []
    series_total_days = 0

    if include_plans:
        sorted_plans = _get_sorted_active_plans(row.plans)
        for plan in sorted_plans:
            plan_dto = _plan_to_dto(plan)
            plans_dtos.append(plan_dto)
            series_total_days += plan_dto.total_days

    return SeriesDTO(
        id=row.id,
        metadata=_metadata_to_dtos(row.metadata_entries),
        image=_generate_image_url(row.image),
        image_key=row.image,
        author_id=row.author_id,
        featured=bool(row.featured),
        status=_to_plan_status(row.status),
        plans=plans_dtos,
        total_days=series_total_days,
    )


def get_filtered_series(
    search: Optional[str],
    skip: int,
    limit: int,
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
        )

    series_dtos: List[SeriesDTO] = [_series_to_dto(row) for row in rows]
    return SeriesListResponse(
        series=series_dtos,
        skip=skip,
        limit=limit,
        total=total,
    )


def get_series_detail(series_id: UUID) -> SeriesDTO:
    with SessionLocal() as db_session:
        row = get_series_by_id(db=db_session, series_id=series_id)
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Series with id '{series_id}' not found",
        )
    return _series_to_dto(row, include_plans=True)

def get_cms_filtered_series(
    token: str,
    search: Optional[str],
    skip: int,
    limit: int,
) -> SeriesListResponse:
    current_author = validate_and_extract_author_details(token=token)
    author_id = None if current_author.is_admin else current_author.id

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
        )

    series_dtos: List[SeriesDTO] = [_series_to_dto(row) for row in rows]
    return SeriesListResponse(
        series=series_dtos,
        skip=skip,
        limit=limit,
        total=total,
    )


def get_cms_series_detail(token: str, series_id: UUID) -> SeriesDTO:
    current_author = validate_and_extract_author_details(token=token)

    with SessionLocal() as db_session:
        row = get_series_by_id(db=db_session, series_id=series_id)

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Series with id '{series_id}' not found",
        )
    if not current_author.is_admin and row.author_id != current_author.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this series",
        )

    return _series_to_dto(row, include_plans=True)

def _validate_plan_ids(
    db,
    plan_ids: List[UUID],
    current_author_id: UUID,
    is_admin: bool,
    current_series_id: Optional[UUID] = None,
) -> None:
    if not plan_ids:
        return

    seen = set()
    unique_ids = [pid for pid in plan_ids if not (pid in seen or seen.add(pid))]

    fetched = get_plans_by_ids(db=db, plan_ids=unique_ids)
    fetched_by_id = {p.id: p for p in fetched}

    for pid in unique_ids:
        plan = fetched_by_id.get(pid)
        if plan is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Plan with id '{pid}' does not exist",
            )
        if plan.deleted_at is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Plan with id '{pid}' does not exist",
            )
        if plan.series_id is not None and plan.series_id != current_series_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Plan with id '{pid}' is already attached to another series",
            )
        if not is_admin and plan.author_id != current_author_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Plan with id '{pid}' belongs to another author",
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
    current_author = validate_and_extract_author_details(token=token)

    try:
        with SessionLocal() as db_session:
            series = get_series_by_id(db=db_session, series_id=series_id)
            if not series:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Series with id '{series_id}' not found",
                )
            if not current_author.is_admin and series.author_id != current_author.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to update this series",
                )

            if update_series_request.plans is not None:
                plan_order_pairs = _build_plan_order_pairs(update_series_request.plans)
                new_plan_ids = [pid for pid, _ in plan_order_pairs]
                current_attached = {p.id for p in (series.plans or []) if p.deleted_at is None}

                if new_plan_ids:
                    _validate_plan_ids(
                        db=db_session,
                        plan_ids=new_plan_ids,
                        current_author_id=current_author.id,
                        is_admin=bool(current_author.is_admin),
                        current_series_id=series_id,
                    )

                new_set = set(new_plan_ids)
                to_detach = list(current_attached - new_set)
                # Every plan in the request gets its display_order (re)written,
                # including ones already attached, since order may have changed.
                plans_to_attach = plan_order_pairs
            else:
                to_detach = []
                plans_to_attach = []

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
            )

            refreshed = get_series_by_id(db=db_session, series_id=series_id)

        return _series_to_dto(refreshed, include_plans=True)
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
    current_author = validate_and_extract_author_details(token=token)

    try:
        with SessionLocal() as db_session:
            series = get_series_by_id(db=db_session, series_id=series_id)
            if not series:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Series with id '{series_id}' not found",
                )
            if not current_author.is_admin and series.author_id != current_author.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to update this series",
                )

            update_series_status(
                db=db_session,
                series=series,
                status=update_series_status_request.status,
                updated_by=current_author.email,
                updated_at=datetime.now(timezone.utc),
            )

            refreshed = get_series_by_id(db=db_session, series_id=series_id)

        return _series_to_dto(refreshed, include_plans=True)
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database integrity error: {exc.orig}",
        ) from exc


def update_existing_series_featured(
    token: str,
    series_id: UUID,
) -> None:
    current_author = validate_and_extract_author_details(token=token)

    try:
        with SessionLocal() as db_session:
            series = get_series_by_id(db=db_session, series_id=series_id)
            if not series:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Series with id '{series_id}' not found",
                )
            if not current_author.is_admin and series.author_id != current_author.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to update this series",
                )

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


def create_new_series(token: str, create_series_request: CreateSeriesRequest) -> SeriesDTO:
    current_author = validate_and_extract_author_details(token=token)

    new_series = Series(
        image=create_series_request.image_key,
        author_id=current_author.id,
        featured=create_series_request.featured if create_series_request.featured is not None else False,
        status=PlanStatus.DRAFT,
    )

    plan_order_pairs = _build_plan_order_pairs(create_series_request.plans)
    plan_ids = [pid for pid, _ in plan_order_pairs]

    try:
        with SessionLocal() as db_session:
            if plan_ids:
                _validate_plan_ids(
                    db=db_session,
                    plan_ids=plan_ids,
                    current_author_id=current_author.id,
                    is_admin=bool(current_author.is_admin),
                )

            saved = save_series_with_plans(
                db=db_session,
                series=new_series,
                metadata_entries=create_series_request.metadata,
                plans_to_attach=plan_order_pairs,
            )

            saved = get_series_by_id(db=db_session, series_id=saved.id)

        return _series_to_dto(saved, include_plans=bool(plan_ids))
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database integrity error: {exc.orig}",
        ) from exc


def delete_existing_series(token: str, series_id: UUID) -> None:
    current_author = validate_and_extract_author_details(token=token)

    try:
        with SessionLocal() as db_session:
            series = get_series_by_id(db=db_session, series_id=series_id)
            if not series:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Series with id '{series_id}' not found",
                )
            if not current_author.is_admin and series.author_id != current_author.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to delete this series",
                )

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