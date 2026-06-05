import json
from typing import List, Optional, Sequence
from uuid import UUID

from sqlalchemy.orm import Session

from pecha_api.config import get
from pecha_api.db.database import SessionLocal
from pecha_api.plans.authors.plan_authors_model import Author
from pecha_api.plans.authors.plan_authors_service import validate_cms_author_details
from pecha_api.plans.groups.groups_repository import get_author_group_ids
from pecha_api.plans.shared.permissions import (
    is_reviewer,
    is_super_admin,
    require_can_read_group_content,
)
from pecha_api.plans.dashboard.dashboard_repository import get_dashboard_items, total_pages
from pecha_api.plans.dashboard.dashboard_response_models import (
    DashboardItemDTO,
    DashboardItemsResponse,
    DashboardPaginationDTO,
    DashboardTab,
)
from pecha_api.plans.plans_enums import PlanStatus
from pecha_api.plans.series.series_repository import get_series_with_plans_by_ids
from pecha_api.plans.series.series_response_models import SeriesMetadataDTO
from pecha_api.plans.series.series_service import _get_sorted_active_plans, _plan_to_dto
from pecha_api.uploads.S3_utils import generate_presigned_access_url


def _parse_languages(item_type: str, languages_raw: Optional[str]) -> List[str]:
    if not languages_raw:
        return []
    if item_type == "plan":
        return [languages_raw]
    return [lang.strip() for lang in languages_raw.split(",") if lang.strip()]


def _to_plan_status(status_value) -> PlanStatus:
    if hasattr(status_value, "value"):
        return PlanStatus(status_value.value)
    return PlanStatus(status_value)


def _image_url(image_key: Optional[str]) -> Optional[str]:
    if not image_key:
        return None
    return generate_presigned_access_url(
        bucket_name=get("AWS_BUCKET_NAME"),
        s3_key=image_key,
    )


def _parse_metadata(raw) -> List[SeriesMetadataDTO]:
    if raw is None:
        return []
    if isinstance(raw, str):
        raw = json.loads(raw)
    if not raw:
        return []
    return [SeriesMetadataDTO(**item) for item in raw]


def _row_to_dto(row) -> DashboardItemDTO:
    item_type = row.item_type
    common = dict(
        id=row.id,
        type=item_type,
        image_url=_image_url(row.image_key),
        image_key=row.image_key,
        status=_to_plan_status(row.status),
        featured=bool(row.featured),
        languages=_parse_languages(item_type, row.languages_raw),
        enrolled_count=int(row.enrolled_count or 0),
        plans_count=int(row.plans_count) if row.plans_count is not None else None,
        updated_at=row.updated_at,
        created_at=row.created_at,
    )
    if item_type == "series":
        return DashboardItemDTO(
            **common,
            metadata=_parse_metadata(row.metadata_json),
            author_id=row.author_id,
        )
    return DashboardItemDTO(
        **common,
        title=row.title or "",
    )


def _resolve_dashboard_group_ids(
    db: Session,
    author: Author,
    group_id: Optional[UUID] = None,
) -> Optional[Sequence[UUID]]:
    if group_id is not None:
        require_can_read_group_content(db=db, group_id=group_id, author=author)
        return [group_id]
    if is_super_admin(author) or is_reviewer(author):
        return None
    return get_author_group_ids(db=db, author_id=author.id)


def _empty_dashboard_response(page: int, page_size: int) -> DashboardItemsResponse:
    return DashboardItemsResponse(
        items=[],
        pagination=DashboardPaginationDTO(
            page=page,
            page_size=page_size,
            total=0,
            total_pages=0,
        ),
    )


def get_dashboard_items_list(
    token: str,
    tab: DashboardTab,
    page: int,
    page_size: int,
    search: Optional[str] = None,
    status: Optional[PlanStatus] = None,
    language: Optional[str] = None,
    featured: Optional[bool] = None,
    group_id: Optional[UUID] = None,
) -> DashboardItemsResponse:
    current_author = validate_cms_author_details(token=token)
    page = max(page, 1)
    page_size = max(page_size, 1)

    with SessionLocal() as db_session:
        group_ids = _resolve_dashboard_group_ids(
            db=db_session,
            author=current_author,
            group_id=group_id,
        )
        if group_ids is not None and len(group_ids) == 0:
            return _empty_dashboard_response(page=page, page_size=page_size)

        rows, total = get_dashboard_items(
            db_session,
            tab=tab,
            page=page,
            page_size=page_size,
            search=search,
            status=status,
            language=language,
            featured=featured,
            group_ids=group_ids,
        )

    items = [_row_to_dto(row) for row in rows]
    return DashboardItemsResponse(
        items=items,
        pagination=DashboardPaginationDTO(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages(total, page_size),
        ),
    )


def _row_to_public_dto(row) -> DashboardItemDTO:
    return _row_to_dto(row).model_copy(update={"author_id": None})


def _published_plans_by_series(db_session, series_ids: List[UUID]) -> dict:
    return {
        series.id: [
            _plan_to_dto(plan)
            for plan in _get_sorted_active_plans(series.plans, published_only=True)
        ]
        for series in get_series_with_plans_by_ids(db_session, series_ids)
    }


def get_practice_items_list(
    tab: DashboardTab,
    page: int,
    page_size: int,
    search: Optional[str] = None,
    language: Optional[str] = None,
    featured: Optional[bool] = None,
) -> DashboardItemsResponse:
    page = max(page, 1)
    page_size = max(page_size, 1)

    with SessionLocal() as db_session:
        rows, total = get_dashboard_items(
            db_session,
            tab=tab,
            page=page,
            page_size=page_size,
            search=search,
            status=PlanStatus.PUBLISHED,
            language=language,
            featured=featured,
            author_id=None,
        )

        items = [_row_to_public_dto(row) for row in rows]
        series_ids = [item.id for item in items if item.type == "series"]
        plans_by_series = _published_plans_by_series(db_session, series_ids)

    for item in items:
        if item.type == "series":
            item.plans = plans_by_series.get(item.id, [])

    return DashboardItemsResponse(
        items=items,
        pagination=DashboardPaginationDTO(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages(total, page_size),
        ),
    )
