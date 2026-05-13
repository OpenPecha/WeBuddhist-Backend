from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from pecha_api.config import get
from pecha_api.db.database import SessionLocal
from pecha_api.plans.plans_enums import DifficultyLevel, PlanStatus
from pecha_api.plans.series.series_model import Series
from pecha_api.plans.series.series_repository import get_series_by_id, get_series_paginated, save_series
from pecha_api.plans.series.service_response_models import (
    CreateSeriesRequest,
    SeriesDTO,
    SeriesPlanDTO,
    SeriesListResponse,
)
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
        tags=plan.tags or [],
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
        name=row.name or {},
        image=_generate_image_url(row.image),
        image_key=row.image,
        author_id=row.author_id,
        featured=bool(row.featured),
        status=_to_plan_status(row.status),
        plans=plans_dtos,
        total_days=series_total_days,
    )


async def get_filtered_series(
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


def create_new_series(create_series_request: CreateSeriesRequest) -> SeriesDTO:
    new_series = Series(
        name=create_series_request.name,
        image=create_series_request.image,
        author_id=create_series_request.author_id,
        featured=create_series_request.featured if create_series_request.featured is not None else False,
        status=PlanStatus.DRAFT,
        created_by=create_series_request.created_by,
    )
    try:
        with SessionLocal() as db_session:
            saved = save_series(db=db_session, series=new_series)
        return _series_to_dto(saved)
    except IntegrityError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database integrity error: {exc.orig}",
        ) from exc
