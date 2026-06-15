from datetime import date, timedelta
from unittest.mock import MagicMock
from uuid import uuid4

from pecha_api.daily_log.daily_log_repository import get_user_streak


def _query_dates(dates):
    query = MagicMock()
    query.filter.return_value.all.return_value = [
        MagicMock(log_date=log_date) for log_date in dates
    ]
    return query


def test_get_user_streak_returns_one_when_only_today_logged():
    db = MagicMock()
    today = date(2026, 6, 11)
    db.query.return_value = _query_dates([today])

    assert get_user_streak(db=db, user_id=uuid4(), today=today) == 1


def test_get_user_streak_counts_consecutive_days_from_today():
    db = MagicMock()
    today = date(2026, 6, 11)
    streak_dates = {today, today - timedelta(days=1), today - timedelta(days=2)}
    db.query.side_effect = [
        _query_dates([today, today - timedelta(days=1)]),
        _query_dates(streak_dates),
    ]

    assert get_user_streak(db=db, user_id=uuid4(), today=today) == 3


def test_get_user_streak_uses_yesterday_when_today_missing():
    db = MagicMock()
    today = date(2026, 6, 11)
    yesterday = today - timedelta(days=1)
    streak_dates = {yesterday, yesterday - timedelta(days=1)}
    db.query.side_effect = [
        _query_dates([yesterday]),
        _query_dates(streak_dates),
    ]

    assert get_user_streak(db=db, user_id=uuid4(), today=today) == 2
