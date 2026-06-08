from typing import Optional
from uuid import UUID

from pecha_api import config
from pecha_api.cache.cache_enums import CacheType
from pecha_api.cache.cache_repository import get_cache_data, set_cache
from pecha_api.plans.series.series_response_models import SeriesListResponse, SeriesDTO
from pecha_api.utils import Utils


def _series_timeout() -> int:
    return config.get_int("CACHE_SERIES_TIMEOUT")


# ---------------------------------------------------------------------------
# Series list (public, paginated)
# ---------------------------------------------------------------------------

async def get_series_list_cache(
    search: Optional[str],
    skip: int,
    limit: int,
    language: Optional[str],
    group_id: Optional[UUID],
) -> Optional[SeriesListResponse]:
    payload = [search, skip, limit, language, str(group_id), CacheType.SERIES_LIST]
    hashed_key = Utils.generate_hash_key(payload=payload)
    data = await get_cache_data(hash_key=hashed_key)
    if data and isinstance(data, dict):
        return SeriesListResponse(**data)
    return None


async def set_series_list_cache(
    search: Optional[str],
    skip: int,
    limit: int,
    language: Optional[str],
    group_id: Optional[UUID],
    data: SeriesListResponse,
) -> None:
    payload = [search, skip, limit, language, str(group_id), CacheType.SERIES_LIST]
    hashed_key = Utils.generate_hash_key(payload=payload)
    await set_cache(hash_key=hashed_key, value=data, cache_time_out=_series_timeout())


# ---------------------------------------------------------------------------
# Series detail
# ---------------------------------------------------------------------------

async def get_series_detail_cache(
    series_id: UUID,
    language: Optional[str],
) -> Optional[SeriesDTO]:
    payload = [str(series_id), language, CacheType.SERIES_DETAIL]
    hashed_key = Utils.generate_hash_key(payload=payload)
    data = await get_cache_data(hash_key=hashed_key)
    if data and isinstance(data, dict):
        return SeriesDTO(**data)
    return None


async def set_series_detail_cache(
    series_id: UUID,
    language: Optional[str],
    data: SeriesDTO,
) -> None:
    payload = [str(series_id), language, CacheType.SERIES_DETAIL]
    hashed_key = Utils.generate_hash_key(payload=payload)
    await set_cache(hash_key=hashed_key, value=data, cache_time_out=_series_timeout())
