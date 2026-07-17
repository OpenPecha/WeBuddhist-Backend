from unittest.mock import AsyncMock, patch

import pytest

from pecha_api.calendar.calendar_cache_service import (
    _get_calendar_year_cache_key,
    get_calendar_year_cache,
    set_calendar_year_cache,
)
from pecha_api.calendar.calendar_parser import CalendarType


def test_cache_keys_are_distinct_by_calendar_type_and_year():
    phugpa_key = _get_calendar_year_cache_key(2025, CalendarType.PHUGPA)
    tsurphu_key = _get_calendar_year_cache_key(2025, CalendarType.TSURPHU)
    next_year_key = _get_calendar_year_cache_key(2026, CalendarType.PHUGPA)

    assert len({phugpa_key, tsurphu_key, next_year_key}) == 3


@pytest.mark.asyncio
async def test_get_calendar_year_cache_returns_dictionary():
    cached_data = {"2025-03-01": {"gregorian_date": "2025-03-01"}}
    with patch(
        "pecha_api.calendar.calendar_cache_service.get_cache_data",
        new_callable=AsyncMock,
        return_value=cached_data,
    ) as get_cache:
        result = await get_calendar_year_cache(2025, CalendarType.PHUGPA)

    assert result == cached_data
    get_cache.assert_awaited_once_with(
        hash_key=_get_calendar_year_cache_key(2025, CalendarType.PHUGPA)
    )


@pytest.mark.asyncio
async def test_set_calendar_year_cache_uses_calendar_timeout():
    calendar_data = {"2025-03-01": {"gregorian_date": "2025-03-01"}}
    with (
        patch(
            "pecha_api.calendar.calendar_cache_service.config.get_int",
            return_value=2592000,
        ),
        patch(
            "pecha_api.calendar.calendar_cache_service.set_cache",
            new_callable=AsyncMock,
            return_value=True,
        ) as set_cache,
    ):
        result = await set_calendar_year_cache(
            2025,
            CalendarType.TSURPHU,
            calendar_data,
        )

    assert result is True
    set_cache.assert_awaited_once_with(
        hash_key=_get_calendar_year_cache_key(2025, CalendarType.TSURPHU),
        value=calendar_data,
        cache_time_out=2592000,
    )
