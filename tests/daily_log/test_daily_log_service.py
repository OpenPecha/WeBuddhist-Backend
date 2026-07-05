from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from fastapi import HTTPException

from pecha_api.daily_log.daily_log_service import (
    _today_for_timezone,
    calculate_streak,
    get_user_streak_service,
    record_daily_log_if_needed,
)


def test_today_for_timezone_defaults_to_utc_date():
    assert isinstance(_today_for_timezone(), date)


def test_calculate_streak_returns_zero_when_no_logs_exist():
    today = date(2026, 6, 11)

    assert calculate_streak(log_dates=set(), today=today) == 0


def test_calculate_streak_returns_one_when_only_today_logged():
    today = date(2026, 6, 11)
    log_dates = {today}

    assert calculate_streak(log_dates=log_dates, today=today) == 1


def test_calculate_streak_counts_consecutive_days_from_today():
    today = date(2026, 6, 11)
    log_dates = {
        today,
        today - timedelta(days=1),
        today - timedelta(days=2),
        today - timedelta(days=4),
    }

    assert calculate_streak(log_dates=log_dates, today=today) == 3


def test_calculate_streak_uses_yesterday_when_today_missing():
    today = date(2026, 6, 11)
    yesterday = today - timedelta(days=1)
    log_dates = {yesterday, yesterday - timedelta(days=1)}

    assert calculate_streak(log_dates=log_dates, today=today) == 2


@pytest.mark.asyncio
async def test_record_daily_log_if_needed_skips_when_cache_hit():
    user_id = uuid4()
    today = date(2026, 6, 11)

    with patch("pecha_api.daily_log.daily_log_service._today_for_timezone", return_value=today), \
         patch("pecha_api.daily_log.daily_log_service.is_user_logged_today_in_cache", return_value=True) as mock_cache, \
         patch("pecha_api.daily_log.daily_log_service.SessionLocal") as mock_session:
        await record_daily_log_if_needed(user_id=user_id, timezone_name="Asia/Kathmandu")

        mock_cache.assert_awaited_once_with(
            user_id=user_id,
            log_date=today,
            timezone_name="Asia/Kathmandu",
        )
        mock_session.assert_not_called()


@pytest.mark.asyncio
async def test_record_daily_log_if_needed_saves_when_not_cached_or_logged():
    user_id = uuid4()
    today = date(2026, 6, 11)
    mock_db = MagicMock()
    mock_db.__enter__ = MagicMock(return_value=mock_db)
    mock_db.__exit__ = MagicMock(return_value=False)

    with patch("pecha_api.daily_log.daily_log_service._today_for_timezone", return_value=today), \
         patch("pecha_api.daily_log.daily_log_service.is_user_logged_today_in_cache", return_value=False), \
         patch("pecha_api.daily_log.daily_log_service.SessionLocal", return_value=mock_db), \
         patch("pecha_api.daily_log.daily_log_service.has_log_for_date", return_value=False) as mock_has_log, \
         patch("pecha_api.daily_log.daily_log_service.save_daily_log") as mock_save, \
         patch("pecha_api.daily_log.daily_log_service.set_user_daily_log_cache") as mock_set_cache, \
         patch("pecha_api.daily_log.daily_log_service.invalidate_user_stats_cache", new_callable=AsyncMock) as mock_invalidate:
        await record_daily_log_if_needed(user_id=user_id, timezone_name="Asia/Kathmandu")

        mock_has_log.assert_called_once_with(db=mock_db, user_id=user_id, log_date=today)
        mock_save.assert_called_once_with(db=mock_db, user_id=user_id, log_date=today)
        mock_set_cache.assert_awaited_once_with(
            user_id=user_id,
            log_date=today,
            timezone_name="Asia/Kathmandu",
        )
        mock_invalidate.assert_awaited_once_with(
            user_id=user_id,
            timezone_name="Asia/Kathmandu",
        )


@pytest.mark.asyncio
async def test_record_daily_log_if_needed_sets_cache_when_db_already_has_log():
    user_id = uuid4()
    today = date(2026, 6, 11)
    mock_db = MagicMock()
    mock_db.__enter__ = MagicMock(return_value=mock_db)
    mock_db.__exit__ = MagicMock(return_value=False)

    with patch("pecha_api.daily_log.daily_log_service._today_for_timezone", return_value=today), \
         patch("pecha_api.daily_log.daily_log_service.is_user_logged_today_in_cache", return_value=False), \
         patch("pecha_api.daily_log.daily_log_service.SessionLocal", return_value=mock_db), \
         patch("pecha_api.daily_log.daily_log_service.has_log_for_date", return_value=True), \
         patch("pecha_api.daily_log.daily_log_service.save_daily_log") as mock_save, \
         patch("pecha_api.daily_log.daily_log_service.set_user_daily_log_cache") as mock_set_cache:
        await record_daily_log_if_needed(user_id=user_id, timezone_name="Asia/Kathmandu")

        mock_save.assert_not_called()
        mock_set_cache.assert_awaited_once_with(
            user_id=user_id,
            log_date=today,
            timezone_name="Asia/Kathmandu",
        )


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
         patch("pecha_api.daily_log.daily_log_service._today_for_timezone", return_value=today), \
         patch("pecha_api.daily_log.daily_log_service.record_daily_log_if_needed", new_callable=AsyncMock) as mock_record, \
         patch("pecha_api.daily_log.daily_log_service.SessionLocal", return_value=mock_db), \
         patch("pecha_api.daily_log.daily_log_service.get_user_streak", return_value=2) as mock_get_streak:
        result = await get_user_streak_service(
            token="test_token",
            timezone_name="Asia/Kathmandu",
        )

        assert result.streak == 2
        mock_record.assert_awaited_once_with(
            user_id=user_id,
            timezone_name="Asia/Kathmandu",
        )
        mock_get_streak.assert_called_once_with(
            db=mock_db,
            user_id=user_id,
            today=today,
        )


@pytest.mark.asyncio
async def test_get_user_stats_service_aggregates_all_sources():
    user_id = uuid4()
    today = date(2026, 6, 11)
    mock_user = MagicMock()
    mock_user.id = user_id
    mock_db = MagicMock()
    mock_db.__enter__ = MagicMock(return_value=mock_db)
    mock_db.__exit__ = MagicMock(return_value=False)

    from pecha_api.daily_log.daily_log_service import get_user_stats_service

    with patch("pecha_api.daily_log.daily_log_service.validate_and_extract_user_details", return_value=mock_user), \
         patch("pecha_api.daily_log.daily_log_service.record_daily_log_if_needed", new_callable=AsyncMock) as mock_record, \
         patch("pecha_api.daily_log.daily_log_service._today_for_timezone", return_value=today), \
         patch("pecha_api.daily_log.daily_log_service.get_user_stats_cache", new_callable=AsyncMock, return_value=None), \
         patch("pecha_api.daily_log.daily_log_service.set_user_stats_cache", new_callable=AsyncMock) as mock_set_stats_cache, \
         patch("pecha_api.daily_log.daily_log_service.SessionLocal", return_value=mock_db), \
         patch("pecha_api.daily_log.daily_log_service.get_user_streak", return_value=3), \
         patch("pecha_api.daily_log.daily_log_service.get_highest_streak", return_value=7), \
         patch("pecha_api.daily_log.daily_log_service.get_week_active_days", return_value=[2, 3, 6]), \
         patch("pecha_api.daily_log.daily_log_service.get_user_activity_totals", return_value=(1200, 10800, 42)):
        result = await get_user_stats_service(
            token="test_token",
            timezone_name="Asia/Kathmandu",
        )

        assert result.streak.current == 3
        assert result.streak.highest == 7
        assert result.streak.week == [2, 3, 6]
        assert result.total_timer == 1200
        assert result.total_accumulated == 10800
        assert result.total_practice_days == 42
        mock_record.assert_awaited_once_with(
            user_id=user_id,
            db=mock_db,
            timezone_name="Asia/Kathmandu",
        )
        mock_set_stats_cache.assert_awaited_once_with(
            user_id=user_id,
            data=result,
            timezone_name="Asia/Kathmandu",
        )


@pytest.mark.asyncio
async def test_get_user_stats_service_returns_cached_stats_without_db_queries():
    user_id = uuid4()
    mock_user = MagicMock()
    mock_user.id = user_id
    cached_stats = MagicMock()

    from pecha_api.daily_log.daily_log_service import get_user_stats_service

    with patch("pecha_api.daily_log.daily_log_service.validate_and_extract_user_details", return_value=mock_user), \
         patch("pecha_api.daily_log.daily_log_service.record_daily_log_if_needed", new_callable=AsyncMock), \
         patch("pecha_api.daily_log.daily_log_service._today_for_timezone", return_value=date(2026, 6, 11)), \
         patch("pecha_api.daily_log.daily_log_service.get_user_stats_cache", new_callable=AsyncMock, return_value=cached_stats), \
         patch("pecha_api.daily_log.daily_log_service.get_user_streak") as mock_streak, \
         patch("pecha_api.daily_log.daily_log_service.set_user_stats_cache", new_callable=AsyncMock) as mock_set_stats_cache:
        result = await get_user_stats_service(
            token="test_token",
            timezone_name="Asia/Kathmandu",
        )

        assert result is cached_stats
        mock_streak.assert_not_called()
        mock_set_stats_cache.assert_not_awaited()
