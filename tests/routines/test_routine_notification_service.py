from datetime import datetime, time, timezone, timedelta

from pecha_api.routines.routine_notifications.routine_notification_repository import (
    RoutineNotificationRow,
)
from pecha_api.routines.routine_notifications.routine_notification_service import (
    _compute_current_day_number,
    _filter_by_utc_time,
    _utc_time_matches,
)
from uuid import uuid4


def test_utc_time_matches_same_minute():
    utc_now = datetime(2026, 6, 23, 3, 45, tzinfo=timezone.utc)
    time_utc = time(3, 45, tzinfo=timezone.utc)

    assert _utc_time_matches(time_utc, utc_now) is True
    assert _utc_time_matches(time(4, 45, tzinfo=timezone.utc), utc_now) is False


def test_filter_by_utc_time_deduplicates_rows():
    user_id = uuid4()
    time_block_id = uuid4()
    utc_now = datetime(2026, 6, 23, 3, 45, tzinfo=timezone.utc)
    source_id = uuid4()
    time_utc = time(3, 45, tzinfo=timezone.utc)

    row = RoutineNotificationRow(
        user_id=user_id,
        time_block_id=time_block_id,
        session_type="PLAN",
        source_id=source_id,
        device_token="token-1",
        platform="android",
        time_block_time_utc=time_utc,
    )
    duplicate = RoutineNotificationRow(
        user_id=user_id,
        time_block_id=time_block_id,
        session_type="PLAN",
        source_id=source_id,
        device_token="token-1",
        platform="android",
        time_block_time_utc=time_utc,
    )

    filtered = _filter_by_utc_time([row, duplicate], utc_now)
    assert len(filtered) == 1


def test_compute_current_day_number_defaults_to_one_without_progress():
    utc_now = datetime(2026, 6, 23, 10, 0, tzinfo=timezone.utc)
    assert _compute_current_day_number(None, utc_now) == 1
