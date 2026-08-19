from datetime import date, datetime, time, timedelta, timezone
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from starlette import status

from pecha_api.timezone_utils import (
    get_date_in_timezone,
    get_day_bounds_in_timezone,
    hhmm_to_time_int,
    local_hhmm_to_utc_time,
    utc_time_to_hhmm,
    utc_time_to_local_hhmm,
)


def test_get_date_in_timezone_defaults_to_utc():
    moment = datetime(2026, 6, 23, 2, 0, tzinfo=timezone.utc)
    assert get_date_in_timezone(None, at=moment) == date(2026, 6, 23)


def test_get_date_in_timezone_uses_client_timezone():
    moment = datetime(2026, 6, 23, 2, 0, tzinfo=timezone.utc)
    los_angeles = timezone(timedelta(hours=-7))

    with patch("pecha_api.timezone_utils._resolve_timezone", return_value=los_angeles):
        assert get_date_in_timezone("America/Los_Angeles", at=moment) == date(2026, 6, 22)


def test_get_date_in_timezone_supports_positive_offset():
    moment = datetime(2026, 6, 22, 20, 0, tzinfo=timezone.utc)
    kathmandu = timezone(timedelta(hours=5, minutes=45))

    with patch("pecha_api.timezone_utils._resolve_timezone", return_value=kathmandu):
        assert get_date_in_timezone("Asia/Kathmandu", at=moment) == date(2026, 6, 23)


def test_get_date_in_timezone_rejects_invalid_timezone():
    with pytest.raises(HTTPException) as exc_info:
        get_date_in_timezone("Not/A_Timezone")

    assert exc_info.value.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "Invalid timezone" in exc_info.value.detail


def test_get_day_bounds_in_timezone_defaults_to_utc():
    moment = datetime(2026, 6, 23, 15, 30, tzinfo=timezone.utc)
    start, end = get_day_bounds_in_timezone(None, at=moment)

    assert start == datetime(2026, 6, 23, 0, 0, tzinfo=timezone.utc)
    assert end == datetime(2026, 6, 23, 23, 59, 59, 999999, tzinfo=timezone.utc)


def test_get_day_bounds_in_timezone_uses_client_timezone():
    moment = datetime(2026, 6, 23, 2, 0, tzinfo=timezone.utc)
    los_angeles = timezone(timedelta(hours=-7))

    with patch("pecha_api.timezone_utils._resolve_timezone", return_value=los_angeles):
        start, end = get_day_bounds_in_timezone("America/Los_Angeles", at=moment)

    assert start == datetime(2026, 6, 22, 0, 0, tzinfo=los_angeles)
    assert end == datetime(2026, 6, 22, 23, 59, 59, 999999, tzinfo=los_angeles)


def test_local_hhmm_to_utc_time_converts_fixed_offset_to_utc():
    kathmandu = timezone(timedelta(hours=5, minutes=45))

    with patch("pecha_api.timezone_utils._resolve_timezone", return_value=kathmandu):
        time_utc = local_hhmm_to_utc_time(
            "09:30",
            "Asia/Kathmandu",
            on_date=datetime(2026, 6, 23, tzinfo=timezone.utc).date(),
        )

    assert utc_time_to_hhmm(time_utc) == "03:45"


def test_utc_time_to_local_hhmm_converts_back_to_local():
    kathmandu = timezone(timedelta(hours=5, minutes=45))
    time_utc = time(3, 45, tzinfo=timezone.utc)

    with patch("pecha_api.timezone_utils._resolve_timezone", return_value=kathmandu):
        assert utc_time_to_local_hhmm(
            time_utc,
            "Asia/Kathmandu",
            on_date=datetime(2026, 6, 23, tzinfo=timezone.utc).date(),
        ) == "09:30"


def test_hhmm_to_time_int():
    assert hhmm_to_time_int("09:30") == 930
    assert hhmm_to_time_int("12:00") == 1200
