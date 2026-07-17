from typing import Any, Dict, Optional

from pecha_api import config
from pecha_api.cache.cache_enums import CacheType
from pecha_api.cache.cache_repository import get_cache_data, set_cache
from pecha_api.utils import Utils

from .calendar_parser import CalendarType

CALENDAR_CACHE_VERSION = "v1"


def _get_calendar_year_cache_key(
    year: int,
    calendar_type: CalendarType,
) -> str:
    payload = [
        CacheType.CALENDAR_YEAR.value,
        CALENDAR_CACHE_VERSION,
        calendar_type.value,
        year,
    ]
    return Utils.generate_hash_key(payload=payload)


async def get_calendar_year_cache(
    year: int,
    calendar_type: CalendarType,
) -> Optional[Dict[str, Dict[str, Any]]]:
    cache_key = _get_calendar_year_cache_key(year, calendar_type)
    cache_data = await get_cache_data(hash_key=cache_key)
    if not isinstance(cache_data, dict):
        return None
    return cache_data


async def set_calendar_year_cache(
    year: int,
    calendar_type: CalendarType,
    data: Dict[str, Dict[str, Any]],
) -> bool:
    cache_key = _get_calendar_year_cache_key(year, calendar_type)
    cache_timeout = config.get_int("CACHE_CALENDAR_TIMEOUT")
    return await set_cache(
        hash_key=cache_key,
        value=data,
        cache_time_out=cache_timeout,
    )
