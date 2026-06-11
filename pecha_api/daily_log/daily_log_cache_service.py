from datetime import date, datetime, timedelta, timezone
from uuid import UUID

from pecha_api.cache.cache_enums import CacheType
from pecha_api.cache.cache_repository import exists_in_cache, set_cache
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
