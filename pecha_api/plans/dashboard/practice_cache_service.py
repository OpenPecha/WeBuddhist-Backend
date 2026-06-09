from typing import Optional

from pecha_api import config
from pecha_api.cache.cache_enums import CacheType
from pecha_api.cache.cache_repository import get_cache_data, set_cache
from pecha_api.plans.dashboard.dashboard_response_models import DashboardItemsResponse, DashboardTab
from pecha_api.utils import Utils


def _practice_timeout() -> int:
    return config.get_int("CACHE_PLAN_TIMEOUT")


async def get_practice_items_cache(
    tab: DashboardTab,
    page: int,
    page_size: int,
    search: Optional[str],
    language: Optional[str],
    featured: Optional[bool],
) -> Optional[DashboardItemsResponse]:
    payload = [tab, page, page_size, search, language, featured, CacheType.PRACTICE_ITEMS]
    hashed_key = Utils.generate_hash_key(payload=payload)
    data = await get_cache_data(hash_key=hashed_key)
    if data and isinstance(data, dict):
        return DashboardItemsResponse(**data)
    return None


async def set_practice_items_cache(
    tab: DashboardTab,
    page: int,
    page_size: int,
    search: Optional[str],
    language: Optional[str],
    featured: Optional[bool],
    data: DashboardItemsResponse,
) -> None:
    payload = [tab, page, page_size, search, language, featured, CacheType.PRACTICE_ITEMS]
    hashed_key = Utils.generate_hash_key(payload=payload)
    await set_cache(hash_key=hashed_key, value=data, cache_time_out=_practice_timeout())
