from datetime import datetime, timedelta, timezone
from uuid import uuid4

from pecha_api.routines.routine_notifications.routine_notification_repository import (
    RoutineNotificationRow,
)
from pecha_api.routines.routine_notifications.routine_notification_service import (
    _compute_current_day_number,
    _filter_by_local_time,
    _local_time_matches,
)


def test_local_time_matches_prefers_routine_timezone():
    utc_now = datetime(2026, 6, 23, 9, 30, tzinfo=timezone.utc)
    created_at = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)

    assert _local_time_matches("UTC", created_at, "09:30", utc_now) is True
    assert _local_time_matches("UTC", created_at, "10:30", utc_now) is False


def test_local_time_matches_using_created_at_offset_fallback():
    created_at = datetime(2026, 1, 1, 8, 0, tzinfo=timezone(timedelta(hours=5, minutes=30)))
    utc_now = datetime(2026, 6, 23, 4, 0, tzinfo=timezone.utc)

    assert _local_time_matches(None, created_at, "09:30", utc_now) is True
    assert _local_time_matches(None, created_at, "10:30", utc_now) is False


def test_filter_by_local_time_deduplicates_rows():
    user_id = uuid4()
    time_block_id = uuid4()
    created_at = datetime(2026, 1, 1, 8, 0, tzinfo=timezone(timedelta(hours=5, minutes=30)))
    utc_now = datetime(2026, 6, 23, 4, 0, tzinfo=timezone.utc)
    source_id = uuid4()

    row = RoutineNotificationRow(
        user_id=user_id,
        routine_timezone=None,
        time_block_id=time_block_id,
        time_block_time="09:30",
        time_block_created_at=created_at,
        session_type="PLAN",
        source_id=source_id,
        device_token="token-1",
        platform="android",
    )
    duplicate = RoutineNotificationRow(
        user_id=user_id,
        routine_timezone=None,
        time_block_id=time_block_id,
        time_block_time="09:30",
        time_block_created_at=created_at,
        session_type="PLAN",
        source_id=source_id,
        device_token="token-1",
        platform="android",
    )

    filtered = _filter_by_local_time([row, duplicate], utc_now)
    assert len(filtered) == 1


def test_compute_current_day_number_defaults_to_one_without_progress():
    utc_now = datetime(2026, 6, 23, 10, 0, tzinfo=timezone.utc)
    assert _compute_current_day_number(None, utc_now) == 1
