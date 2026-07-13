import asyncio
from datetime import date, datetime, timezone
from typing import Optional
from uuid import UUID

from pecha_api import config
from pecha_api.cache.cache_enums import CacheType
from pecha_api.cache.cache_repository import delete_cache, exists_in_cache, get_cache_data, set_cache
from pecha_api.daily_log.daily_log_response_models import UserStatsResponse
from pecha_api.timezone_utils import get_day_bounds_in_timezone
from pecha_api.utils import Utils

_DAILY_LOG_CACHE_VALUE = "logged"


def _build_daily_log_cache_key(user_id: UUID, log_date: date) -> str:
    payload = [str(user_id), str(log_date), CacheType.USER_DAILY_LOG.value]
    return Utils.generate_hash_key(payload)


def _timezone_cache_suffix(timezone_name: Optional[str]) -> str:
    if not timezone_name or not timezone_name.strip():
        return "UTC"
    return timezone_name.strip()


def _seconds_until_end_of_day_in_timezone(timezone_name: Optional[str]) -> int:
    now = datetime.now(timezone.utc)
    _, day_end = get_day_bounds_in_timezone(timezone_name, at=now)
    now_in_timezone = now.astimezone(day_end.tzinfo)
    return max(int((day_end - now_in_timezone).total_seconds()), 1)


async def is_user_logged_today_in_cache(user_id: UUID, log_date: date) -> bool:
    cache_key = _build_daily_log_cache_key(user_id=user_id, log_date=log_date)
    return await exists_in_cache(cache_key)


async def set_user_daily_log_cache(
    user_id: UUID,
    log_date: date,
    timezone_name: Optional[str] = None,
) -> None:
    cache_key = _build_daily_log_cache_key(user_id=user_id, log_date=log_date)
    await set_cache(
        hash_key=cache_key,
        value=_DAILY_LOG_CACHE_VALUE,
        cache_time_out=_seconds_until_end_of_day_in_timezone(timezone_name),
    )


def _build_user_stats_cache_key(
    user_id: UUID,
    timezone_name: Optional[str] = None,
) -> str:
    payload = [
        str(user_id),
        CacheType.USER_STATS.value,
        _timezone_cache_suffix(timezone_name),
    ]
    return Utils.generate_hash_key(payload)


async def get_user_stats_cache(
    user_id: UUID,
    timezone_name: Optional[str] = None,
) -> Optional[UserStatsResponse]:
    cache_key = _build_user_stats_cache_key(
        user_id=user_id,
        timezone_name=timezone_name,
    )
    cache_data = await get_cache_data(hash_key=cache_key)
    if cache_data and isinstance(cache_data, dict):
        return UserStatsResponse(**cache_data)
    return None


async def set_user_stats_cache(
    user_id: UUID,
    data: UserStatsResponse,
    timezone_name: Optional[str] = None,
) -> None:
    cache_key = _build_user_stats_cache_key(
        user_id=user_id,
        timezone_name=timezone_name,
    )
    cache_time_out = config.get_int("CACHE_USER_STATS_TIMEOUT")
    await set_cache(hash_key=cache_key, value=data, cache_time_out=cache_time_out)


async def invalidate_user_stats_cache(
    user_id: UUID,
    timezone_name: Optional[str] = None,
) -> None:
    cache_key = _build_user_stats_cache_key(
        user_id=user_id,
        timezone_name=timezone_name,
    )
    await delete_cache(hash_key=cache_key)


def schedule_invalidate_user_stats_cache(
    user_id: UUID,
    timezone_name: Optional[str] = None,
) -> None:
    """Invalidate stats cache from sync callers without blocking."""
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(
            invalidate_user_stats_cache(user_id=user_id, timezone_name=timezone_name)
        )
    except RuntimeError:
        asyncio.run(
            invalidate_user_stats_cache(user_id=user_id, timezone_name=timezone_name)
        )
