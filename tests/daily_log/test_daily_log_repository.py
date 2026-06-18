from datetime import date, timedelta
from unittest.mock import MagicMock
from uuid import uuid4

from pecha_api.daily_log.daily_log_repository import (
    get_highest_streak,
    get_user_streak,
    get_week_active_days,
)


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


def _week_db(captured):
    """Mock DB that records the lower-bound (week_start) of the date filter so
    tests can assert the Monday boundary, and returns a fixed distinct count."""
    db = MagicMock()

    def filter_side_effect(*conditions):
        # conditions[1] is `UserDailyLog.log_date >= week_start`
        captured["week_start"] = conditions[1].right.value
        result = MagicMock()
        result.distinct.return_value.count.return_value = 4
        return result

    db.query.return_value.filter.side_effect = filter_side_effect
    return db


def test_get_week_active_days_uses_monday_as_week_start():
    captured = {}
    # 2026-06-11 is a Thursday; that week's Monday is 2026-06-08.
    thursday = date(2026, 6, 11)
    db = _week_db(captured)

    assert get_week_active_days(db=db, user_id=uuid4(), today=thursday) == 4
    assert captured["week_start"] == date(2026, 6, 8)


def test_get_week_active_days_week_start_is_today_when_today_is_monday():
    captured = {}
    monday = date(2026, 6, 8)
    db = _week_db(captured)

    assert get_week_active_days(db=db, user_id=uuid4(), today=monday) == 4
    assert captured["week_start"] == monday


def test_get_highest_streak_returns_zero_when_no_logs():
    db = MagicMock()
    db.query.return_value.filter.return_value.all.return_value = []

    assert get_highest_streak(db=db, user_id=uuid4()) == 0


def test_get_highest_streak_finds_longest_run():
    db = MagicMock()
    anchor = date(2026, 6, 11)
    # Two runs: a 2-day run, then a 4-day run after a gap.
    dates = [
        anchor,
        anchor - timedelta(days=1),
        anchor - timedelta(days=5),
        anchor - timedelta(days=6),
        anchor - timedelta(days=7),
        anchor - timedelta(days=8),
    ]
    db.query.return_value.filter.return_value.all.return_value = [
        MagicMock(log_date=d) for d in dates
    ]

    assert get_highest_streak(db=db, user_id=uuid4()) == 4
