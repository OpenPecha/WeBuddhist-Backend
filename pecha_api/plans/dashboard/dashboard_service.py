from typing import List, Optional

from pecha_api.config import get
from pecha_api.db.database import SessionLocal
from pecha_api.plans.authors.plan_authors_service import validate_and_extract_author_details
from pecha_api.plans.dashboard.dashboard_repository import get_dashboard_items, total_pages
from pecha_api.plans.dashboard.dashboard_response_models import (
    DashboardItemDTO,
    DashboardItemsResponse,
    DashboardPaginationDTO,
    DashboardTab,
)
from pecha_api.plans.plans_enums import PlanStatus
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


def _row_to_dto(row) -> DashboardItemDTO:
    item_type = row.item_type
    return DashboardItemDTO(
        id=row.id,
        type=item_type,
        title=row.title or "",
        image_url=_image_url(row.image_key),
        status=_to_plan_status(row.status),
        featured=bool(row.featured),
        languages=_parse_languages(item_type, row.languages_raw),
        enrolled_count=int(row.enrolled_count or 0),
        plans_count=int(row.plans_count) if row.plans_count is not None else None,
        updated_at=row.updated_at,
        created_at=row.created_at,
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
) -> DashboardItemsResponse:
    current_author = validate_and_extract_author_details(token=token)
    author_id = None if current_author.is_admin else current_author.id

    page = max(page, 1)
    page_size = max(page_size, 1)

    with SessionLocal() as db_session:
        rows, total = get_dashboard_items(
            db_session,
            tab=tab,
            page=page,
            page_size=page_size,
            search=search,
            status=status,
            language=language,
            featured=featured,
            author_id=author_id,
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
