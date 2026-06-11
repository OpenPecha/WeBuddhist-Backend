from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from pecha_api.daily_log.daily_log_cache_service import (
    _seconds_until_end_of_utc_day,
    is_user_logged_today_in_cache,
    set_user_daily_log_cache,
)


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
