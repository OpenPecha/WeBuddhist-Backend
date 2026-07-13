from collections import defaultdict
from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from starlette import status

from pecha_api.db.database import SessionLocal
from pecha_api.plans.authors.plan_authors_service import validate_and_extract_author_details
from pecha_api.plans.shared.permissions import require_super_admin, require_super_admin_or_reviewer
from pecha_api.region_restrictions.region_restriction_enums import RestrictedItemType
from pecha_api.region_restrictions.region_restriction_item_lookup import (
    resolve_titles_for_rows,
    search_restriction_candidates,
)
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
    ChinaRestrictionCandidateListResponse,
    CreateChinaRestrictedItemRequest,
)
from pecha_api.region_restrictions.region_restriction_service import clear_restricted_items_cache


def _normalize_item_type(raw_type) -> RestrictedItemType:
    if isinstance(raw_type, RestrictedItemType):
        return raw_type
    return RestrictedItemType(raw_type)


def _row_to_dto(
    row: ChinaRestrictedItem,
    *,
    title: Optional[str] = None,
    subtitle: Optional[str] = None,
) -> ChinaRestrictedItemDTO:
    item_type = _normalize_item_type(row.item_type)
    return ChinaRestrictedItemDTO(
        id=row.id,
        item_type=item_type,
        item_id=row.item_id,
        title=title,
        subtitle=subtitle,
        created_at=row.created_at.isoformat() if row.created_at else "",
        updated_at=row.updated_at.isoformat() if row.updated_at else None,
    )


def _enrich_rows(db, rows: list[ChinaRestrictedItem]) -> list[ChinaRestrictedItemDTO]:
    ids_by_type: dict[RestrictedItemType, list[UUID]] = defaultdict(list)
    for row in rows:
        ids_by_type[_normalize_item_type(row.item_type)].append(row.item_id)

    titles_by_type: dict[RestrictedItemType, dict[UUID, str]] = {}
    for item_type, item_ids in ids_by_type.items():
        titles_by_type[item_type] = resolve_titles_for_rows(
            db,
            item_type=item_type,
            item_ids=item_ids,
        )

    return [
        _row_to_dto(
            row,
            title=titles_by_type.get(_normalize_item_type(row.item_type), {}).get(
                row.item_id
            ),
        )
        for row in rows
    ]


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
        items = _enrich_rows(db, rows)
    return ChinaRestrictedItemListResponse(
        items=items,
        skip=skip,
        limit=limit,
        total=total,
    )


def search_admin_china_restriction_candidates(
    token: str,
    item_type: RestrictedItemType,
    search: Optional[str],
    skip: int,
    limit: int,
) -> ChinaRestrictionCandidateListResponse:
    author = validate_and_extract_author_details(token=token)
    require_super_admin_or_reviewer(author)
    with SessionLocal() as db:
        items, total = search_restriction_candidates(
            db=db,
            item_type=item_type,
            search=search,
            skip=skip,
            limit=limit,
        )
    return ChinaRestrictionCandidateListResponse(
        items=items,
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
        titles = resolve_titles_for_rows(
            db,
            item_type=body.item_type,
            item_ids=[body.item_id],
        )
        dto = _row_to_dto(row, title=titles.get(body.item_id))
    clear_restricted_items_cache()
    return dto


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
