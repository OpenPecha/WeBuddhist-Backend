import asyncio
from datetime import date, datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from pecha_api import config
from pecha_api.cache.cache_enums import CacheType
from pecha_api.cache.cache_repository import delete_cache, exists_in_cache, get_cache_data, set_cache
from pecha_api.daily_log.daily_log_response_models import UserStatsResponse
from pecha_api.utils import Utils

_DAILY_LOG_CACHE_VALUE = "logged"


def _build_daily_log_cache_key(user_id: UUID, log_date: date) -> str:
    payload = [str(user_id), str(log_date), CacheType.USER_DAILY_LOG.value]
    return Utils.generate_hash_key(payload)


def _seconds_until_end_of_utc_day() -> int:
    now = datetime.now(timezone.utc)
    tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return max(int((tomorrow - now).total_seconds()), 1)


async def is_user_logged_today_in_cache(user_id: UUID, log_date: date) -> bool:
    cache_key = _build_daily_log_cache_key(user_id=user_id, log_date=log_date)
    return await exists_in_cache(cache_key)


async def set_user_daily_log_cache(user_id: UUID, log_date: date) -> None:
    cache_key = _build_daily_log_cache_key(user_id=user_id, log_date=log_date)
    await set_cache(
        hash_key=cache_key,
        value=_DAILY_LOG_CACHE_VALUE,
        cache_time_out=_seconds_until_end_of_utc_day(),
    )


def _build_user_stats_cache_key(user_id: UUID) -> str:
    payload = [str(user_id), CacheType.USER_STATS.value]
    return Utils.generate_hash_key(payload)


async def get_user_stats_cache(user_id: UUID) -> Optional[UserStatsResponse]:
    cache_key = _build_user_stats_cache_key(user_id=user_id)
    cache_data = await get_cache_data(hash_key=cache_key)
    if cache_data and isinstance(cache_data, dict):
        return UserStatsResponse(**cache_data)
    return None


async def set_user_stats_cache(user_id: UUID, data: UserStatsResponse) -> None:
    cache_key = _build_user_stats_cache_key(user_id=user_id)
    cache_time_out = config.get_int("CACHE_USER_STATS_TIMEOUT")
    await set_cache(hash_key=cache_key, value=data, cache_time_out=cache_time_out)


async def invalidate_user_stats_cache(user_id: UUID) -> None:
    cache_key = _build_user_stats_cache_key(user_id=user_id)
    await delete_cache(hash_key=cache_key)


def schedule_invalidate_user_stats_cache(user_id: UUID) -> None:
    """Invalidate stats cache from sync callers without blocking."""
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(invalidate_user_stats_cache(user_id))
    except RuntimeError:
        asyncio.run(invalidate_user_stats_cache(user_id))
