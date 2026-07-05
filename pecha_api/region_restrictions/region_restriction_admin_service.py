from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from starlette import status

from pecha_api.db.database import SessionLocal
from pecha_api.plans.authors.plan_authors_service import validate_and_extract_author_details
from pecha_api.plans.shared.permissions import require_super_admin, require_super_admin_or_reviewer
from pecha_api.region_restrictions.region_restriction_enums import RestrictedItemType
from pecha_api.region_restrictions.region_restriction_models import ChinaRestrictedItem
from pecha_api.region_restrictions.region_restriction_repository import (
    create_china_restricted_item,
    delete_china_restricted_item_by_id,
    is_item_restricted_in_china,
    list_china_restricted_items,
)
from pecha_api.region_restrictions.region_restriction_response_models import (
    ChinaRestrictedItemDTO,
    ChinaRestrictedItemListResponse,
    CreateChinaRestrictedItemRequest,
)
from pecha_api.region_restrictions.region_restriction_service import clear_restricted_items_cache


def _row_to_dto(row: ChinaRestrictedItem) -> ChinaRestrictedItemDTO:
    item_type = (
        row.item_type
        if isinstance(row.item_type, RestrictedItemType)
        else RestrictedItemType(row.item_type)
    )
    return ChinaRestrictedItemDTO(
        id=row.id,
        item_type=item_type,
        item_id=row.item_id,
        created_at=row.created_at.isoformat() if row.created_at else "",
        updated_at=row.updated_at.isoformat() if row.updated_at else None,
    )


def list_admin_china_restricted_items(
    token: str,
    skip: int,
    limit: int,
    item_type: Optional[RestrictedItemType] = None,
) -> ChinaRestrictedItemListResponse:
    author = validate_and_extract_author_details(token=token)
    require_super_admin_or_reviewer(author)
    with SessionLocal() as db:
        rows, total = list_china_restricted_items(
            db=db,
            skip=skip,
            limit=limit,
            item_type=item_type,
        )
    return ChinaRestrictedItemListResponse(
        items=[_row_to_dto(row) for row in rows],
        skip=skip,
        limit=limit,
        total=total,
    )


def create_admin_china_restricted_item(
    token: str,
    body: CreateChinaRestrictedItemRequest,
) -> ChinaRestrictedItemDTO:
    author = validate_and_extract_author_details(token=token)
    require_super_admin(author)
    with SessionLocal() as db:
        if is_item_restricted_in_china(
            db=db,
            item_type=body.item_type,
            item_id=body.item_id,
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Item is already restricted in China",
            )
        row = create_china_restricted_item(
            db=db,
            item_type=body.item_type,
            item_id=body.item_id,
        )
    clear_restricted_items_cache()
    return _row_to_dto(row)


def delete_admin_china_restricted_item(token: str, row_id: UUID) -> None:
    author = validate_and_extract_author_details(token=token)
    require_super_admin(author)
    with SessionLocal() as db:
        deleted = delete_china_restricted_item_by_id(db=db, row_id=row_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restricted item not found",
        )
    clear_restricted_items_cache()
