from collections import defaultdict
from functools import lru_cache
from typing import Callable, Iterable, Optional, TypeVar
from uuid import UUID

from fastapi import HTTPException
from starlette import status

from pecha_api.db.database import SessionLocal
from pecha_api.region_restrictions.china_timezone import is_china_timezone
from pecha_api.region_restrictions.region_restriction_enums import RestrictedItemType
from pecha_api.region_restrictions.region_restriction_repository import (
    get_all_china_restricted_items,
)

T = TypeVar("T")


@lru_cache(maxsize=1)
def _load_restricted_item_ids_by_type() -> dict[str, frozenset[UUID]]:
    with SessionLocal() as db:
        rows = get_all_china_restricted_items(db=db)

    grouped: dict[str, set[UUID]] = defaultdict(set)
    for row in rows:
        item_type = (
            row.item_type.value
            if hasattr(row.item_type, "value")
            else str(row.item_type)
        )
        grouped[item_type].add(row.item_id)
    return {item_type: frozenset(item_ids) for item_type, item_ids in grouped.items()}


def clear_restricted_items_cache() -> None:
    _load_restricted_item_ids_by_type.cache_clear()


def get_restricted_item_ids(item_type: RestrictedItemType) -> frozenset[UUID]:
    return _load_restricted_item_ids_by_type().get(item_type.value, frozenset())


def is_restricted_in_china(item_type: RestrictedItemType, item_id: UUID) -> bool:
    return item_id in get_restricted_item_ids(item_type)


def should_hide_for_timezone(
    timezone_name: Optional[str],
    item_type: RestrictedItemType,
    item_id: UUID,
) -> bool:
    return is_china_timezone(timezone_name) and is_restricted_in_china(item_type, item_id)


def filter_items_for_timezone(
    items: Iterable[T],
    *,
    timezone_name: Optional[str],
    item_type: RestrictedItemType,
    id_of: Callable[[T], UUID],
) -> list[T]:
    if not is_china_timezone(timezone_name):
        return list(items)

    restricted_ids = get_restricted_item_ids(item_type)
    if not restricted_ids:
        return list(items)

    return [item for item in items if id_of(item) not in restricted_ids]


def assert_visible_for_timezone(
    *,
    timezone_name: Optional[str],
    item_type: RestrictedItemType,
    item_id: UUID,
    not_found_detail: str = "Not found",
) -> None:
    if should_hide_for_timezone(timezone_name, item_type, item_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=not_found_detail,
        )
