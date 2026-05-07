from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException
from pecha_api.config import get
from pecha_api.db.database import SessionLocal
from pecha_api.plans.plans_enums import DifficultyLevel, PlanStatus
from pecha_api.plans.series.series_model import Series
from pecha_api.plans.series.series_repository import get_series_by_id, get_series_paginated, save_series
from pecha_api.plans.series.service_response_models import (
    CreateSeriesRequest,
    SeriesDTO,
    SeriesListResponse,
)
from pecha_api.uploads.S3_utils import generate_presigned_access_url
from starlette import status


def _series_to_dto(row: Series) -> SeriesDTO:
    image_key = row.image
    image_url = None
    if image_key:
        image_url = generate_presigned_access_url(
            bucket_name=get("AWS_BUCKET_NAME"),
            s3_key=image_key,
        )
    status_value = row.status
    status_enum = (
        PlanStatus(status_value.value)
        if hasattr(status_value, "value")
        else PlanStatus(status_value)
    )
    return SeriesDTO(
        id=row.id,
        name=row.name or {},
        image=image_url,
        image_key=image_key,
        author_id=row.author_id,
        featured=bool(row.featured),
        status=status_enum,
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
    return _series_to_dto(row)


def create_new_series(create_series_request: CreateSeriesRequest) -> SeriesDTO:
    new_series = Series(
        name=create_series_request.name,
        image=create_series_request.image,
        author_id=create_series_request.author_id,
        featured=create_series_request.featured if create_series_request.featured is not None else False,
        status=PlanStatus.DRAFT,
        created_by=create_series_request.created_by,
    )
    with SessionLocal() as db_session:
        saved = save_series(db=db_session, series=new_series)
    return _series_to_dto(saved)
