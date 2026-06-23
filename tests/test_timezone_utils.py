from datetime import date, datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from starlette import status

from pecha_api.timezone_utils import get_date_in_timezone


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
