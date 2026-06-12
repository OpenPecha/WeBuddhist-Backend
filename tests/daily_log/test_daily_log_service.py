from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from fastapi import HTTPException

from pecha_api.daily_log.daily_log_service import (
    _utc_today,
    calculate_streak,
    get_user_streak_service,
    register_daily_log_service,
    record_daily_log_if_needed,
)


def test_utc_today_returns_current_utc_date():
    assert isinstance(_utc_today(), date)


def test_calculate_streak_returns_zero_when_no_logs_exist():
    today = date(2026, 6, 11)

    with patch("pecha_api.daily_log.daily_log_service._utc_today", return_value=today):
        assert calculate_streak(log_dates=set()) == 0


def test_calculate_streak_returns_zero_when_yesterday_missing():
    today = date(2026, 6, 11)
    log_dates = {today}

    with patch("pecha_api.daily_log.daily_log_service._utc_today", return_value=today):
        assert calculate_streak(log_dates=log_dates) == 0


def test_calculate_streak_counts_consecutive_days_from_today():
    today = date(2026, 6, 11)
    log_dates = {
        today,
        today - timedelta(days=1),
        today - timedelta(days=2),
        today - timedelta(days=4),
    }

    with patch("pecha_api.daily_log.daily_log_service._utc_today", return_value=today):
        assert calculate_streak(log_dates=log_dates) == 3


def test_calculate_streak_uses_yesterday_when_today_missing():
    today = date(2026, 6, 11)
    yesterday = today - timedelta(days=1)
    log_dates = {yesterday, yesterday - timedelta(days=1)}

    with patch("pecha_api.daily_log.daily_log_service._utc_today", return_value=today):
        assert calculate_streak(log_dates=log_dates) == 2


@pytest.mark.asyncio
async def test_register_daily_log_service_validates_user_and_records_log():
    user_id = uuid4()
    mock_user = MagicMock()
    mock_user.id = user_id

    with patch("pecha_api.daily_log.daily_log_service.validate_and_extract_user_details", return_value=mock_user), \
         patch("pecha_api.daily_log.daily_log_service.record_daily_log_if_needed", new_callable=AsyncMock) as mock_record:
        await register_daily_log_service(token="test_token")

        mock_record.assert_awaited_once_with(user_id=user_id)


@pytest.mark.asyncio
async def test_register_daily_log_service_raises_for_invalid_token():
    with patch(
        "pecha_api.daily_log.daily_log_service.validate_and_extract_user_details",
        side_effect=HTTPException(status_code=401, detail="Invalid token"),
    ), patch(
        "pecha_api.daily_log.daily_log_service.record_daily_log_if_needed",
        new_callable=AsyncMock,
    ) as mock_record:
        with pytest.raises(HTTPException) as exc_info:
            await register_daily_log_service(token="bad_token")

        assert exc_info.value.status_code == 401
        mock_record.assert_not_awaited()


@pytest.mark.asyncio
async def test_record_daily_log_if_needed_skips_when_cache_hit():
    user_id = uuid4()
    today = date(2026, 6, 11)

    with patch("pecha_api.daily_log.daily_log_service._utc_today", return_value=today), \
         patch("pecha_api.daily_log.daily_log_service.is_user_logged_today_in_cache", return_value=True) as mock_cache, \
         patch("pecha_api.daily_log.daily_log_service.SessionLocal") as mock_session:
        await record_daily_log_if_needed(user_id=user_id)

        mock_cache.assert_awaited_once_with(user_id=user_id, log_date=today)
        mock_session.assert_not_called()


@pytest.mark.asyncio
async def test_record_daily_log_if_needed_saves_when_not_cached_or_logged():
    user_id = uuid4()
    today = date(2026, 6, 11)
    mock_db = MagicMock()
    mock_db.__enter__ = MagicMock(return_value=mock_db)
    mock_db.__exit__ = MagicMock(return_value=False)

    with patch("pecha_api.daily_log.daily_log_service._utc_today", return_value=today), \
         patch("pecha_api.daily_log.daily_log_service.is_user_logged_today_in_cache", return_value=False), \
         patch("pecha_api.daily_log.daily_log_service.SessionLocal", return_value=mock_db), \
         patch("pecha_api.daily_log.daily_log_service.has_log_for_date", return_value=False) as mock_has_log, \
         patch("pecha_api.daily_log.daily_log_service.save_daily_log") as mock_save, \
         patch("pecha_api.daily_log.daily_log_service.set_user_daily_log_cache") as mock_set_cache:
        await record_daily_log_if_needed(user_id=user_id)

        mock_has_log.assert_called_once_with(db=mock_db, user_id=user_id, log_date=today)
        mock_save.assert_called_once_with(db=mock_db, user_id=user_id, log_date=today)
        mock_set_cache.assert_awaited_once_with(user_id=user_id, log_date=today)


@pytest.mark.asyncio
async def test_record_daily_log_if_needed_sets_cache_when_db_already_has_log():
    user_id = uuid4()
    today = date(2026, 6, 11)
    mock_db = MagicMock()
    mock_db.__enter__ = MagicMock(return_value=mock_db)
    mock_db.__exit__ = MagicMock(return_value=False)

    with patch("pecha_api.daily_log.daily_log_service._utc_today", return_value=today), \
         patch("pecha_api.daily_log.daily_log_service.is_user_logged_today_in_cache", return_value=False), \
         patch("pecha_api.daily_log.daily_log_service.SessionLocal", return_value=mock_db), \
         patch("pecha_api.daily_log.daily_log_service.has_log_for_date", return_value=True), \
         patch("pecha_api.daily_log.daily_log_service.save_daily_log") as mock_save, \
         patch("pecha_api.daily_log.daily_log_service.set_user_daily_log_cache") as mock_set_cache:
        await record_daily_log_if_needed(user_id=user_id)

        mock_save.assert_not_called()
        mock_set_cache.assert_awaited_once_with(user_id=user_id, log_date=today)


@pytest.mark.asyncio
async def test_get_user_streak_service_returns_streak():
    user_id = uuid4()
    today = date(2026, 6, 11)
    mock_user = MagicMock()
    mock_user.id = user_id
    mock_db = MagicMock()
    mock_db.__enter__ = MagicMock(return_value=mock_db)
    mock_db.__exit__ = MagicMock(return_value=False)

    with patch("pecha_api.daily_log.daily_log_service.validate_and_extract_user_details", return_value=mock_user), \
         patch("pecha_api.daily_log.daily_log_service.SessionLocal", return_value=mock_db), \
         patch("pecha_api.daily_log.daily_log_service.get_user_streak", return_value=2):
        result = await get_user_streak_service(token="test_token")

        assert result.streak == 2
