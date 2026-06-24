from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from pecha_api.daily_log.daily_log_cache_service import (
    _seconds_until_end_of_utc_day,
    get_user_stats_cache,
    invalidate_user_stats_cache,
    is_user_logged_today_in_cache,
    set_user_daily_log_cache,
    set_user_stats_cache,
)
from pecha_api.daily_log.daily_log_response_models import StreakStats, UserStatsResponse


def test_seconds_until_end_of_utc_day_returns_positive_value():
    fixed_now = datetime(2026, 6, 11, 12, 0, 0, tzinfo=timezone.utc)

    with patch("pecha_api.daily_log.daily_log_cache_service.datetime") as mock_datetime:
        mock_datetime.now.return_value = fixed_now
        mock_datetime.side_effect = lambda *args, **kwargs: datetime(*args, **kwargs)

        seconds = _seconds_until_end_of_utc_day()

    assert seconds == 12 * 60 * 60


@pytest.mark.asyncio
async def test_is_user_logged_today_in_cache_returns_true_when_key_exists():
    user_id = uuid4()
    log_date = date(2026, 6, 11)

    with patch(
        "pecha_api.daily_log.daily_log_cache_service.exists_in_cache",
        new_callable=AsyncMock,
        return_value=True,
    ) as mock_exists:
        result = await is_user_logged_today_in_cache(user_id=user_id, log_date=log_date)

        assert result is True
        mock_exists.assert_awaited_once()


@pytest.mark.asyncio
async def test_is_user_logged_today_in_cache_returns_false_when_key_missing():
    user_id = uuid4()
    log_date = date(2026, 6, 11)

    with patch(
        "pecha_api.daily_log.daily_log_cache_service.exists_in_cache",
        new_callable=AsyncMock,
        return_value=False,
    ):
        result = await is_user_logged_today_in_cache(user_id=user_id, log_date=log_date)

        assert result is False


@pytest.mark.asyncio
async def test_set_user_daily_log_cache_stores_until_end_of_day():
    user_id = uuid4()
    log_date = date(2026, 6, 11)

    with patch(
        "pecha_api.daily_log.daily_log_cache_service._seconds_until_end_of_utc_day",
        return_value=3600,
    ), patch(
        "pecha_api.daily_log.daily_log_cache_service.set_cache",
        new_callable=AsyncMock,
    ) as mock_set_cache:
        await set_user_daily_log_cache(user_id=user_id, log_date=log_date)

        mock_set_cache.assert_awaited_once()
        _, kwargs = mock_set_cache.await_args
        assert kwargs["cache_time_out"] == 3600
        assert kwargs["value"] == "logged"


@pytest.mark.asyncio
async def test_get_user_stats_cache_returns_parsed_response():
    user_id = uuid4()
    stats_payload = {
        "streak": {"current": 2, "highest": 5, "week": [1, 3]},
        "total_timer": 100,
        "total_accumulated": 200,
        "total_practice_days": 3,
    }

    with patch(
        "pecha_api.daily_log.daily_log_cache_service.get_cache_data",
        new_callable=AsyncMock,
        return_value=stats_payload,
    ):
        result = await get_user_stats_cache(user_id=user_id)

    assert isinstance(result, UserStatsResponse)
    assert result.streak.current == 2
    assert result.total_practice_days == 3


@pytest.mark.asyncio
async def test_set_user_stats_cache_uses_five_minute_timeout():
    user_id = uuid4()
    stats = UserStatsResponse(
        streak=StreakStats(current=1, highest=1, week=[1]),
        total_timer=0,
        total_accumulated=0,
        total_practice_days=0,
    )

    with patch(
        "pecha_api.daily_log.daily_log_cache_service.config.get_int",
        return_value=300,
    ), patch(
        "pecha_api.daily_log.daily_log_cache_service.set_cache",
        new_callable=AsyncMock,
    ) as mock_set_cache:
        await set_user_stats_cache(user_id=user_id, data=stats)

        mock_set_cache.assert_awaited_once()
        _, kwargs = mock_set_cache.await_args
        assert kwargs["cache_time_out"] == 300
        assert kwargs["value"] == stats


@pytest.mark.asyncio
async def test_invalidate_user_stats_cache_deletes_key():
    user_id = uuid4()

    with patch(
        "pecha_api.daily_log.daily_log_cache_service.delete_cache",
        new_callable=AsyncMock,
    ) as mock_delete_cache:
        await invalidate_user_stats_cache(user_id=user_id)

        mock_delete_cache.assert_awaited_once()
