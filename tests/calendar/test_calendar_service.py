from datetime import date
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from starlette import status

from pecha_api.calendar.calendar_parser import parse_calendar_year
from pecha_api.calendar.calendar_service import (
    get_calendar_month_service,
    get_calendar_today_service,
    get_calendar_year_service,
)


@pytest.fixture(autouse=True)
def clear_calendar_year_cache():
    parse_calendar_year.cache_clear()
    yield
    parse_calendar_year.cache_clear()


class TestGetCalendarMonthService:
    def test_returns_gregorian_month_with_lunar_dates(self):
        result = get_calendar_month_service(2025, 3)

        assert result.year == 2025
        assert result.month == 3
        assert len(result.days) == 31
        assert result.days[0].gregorian_date == "2025-03-01"
        assert result.days[0].lunar_month is not None

    def test_raises_for_invalid_gregorian_year(self):
        with pytest.raises(HTTPException) as exc_info:
            get_calendar_month_service(1700, 3)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "Gregorian year 1700" in exc_info.value.detail

    def test_raises_for_invalid_gregorian_month(self):
        with pytest.raises(HTTPException) as exc_info:
            get_calendar_month_service(2025, 13)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "between 1 and 12" in exc_info.value.detail

    def test_raises_when_month_has_no_data(self):
        with pytest.raises(HTTPException) as exc_info:
            get_calendar_month_service(1800, 1)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "No calendar data found for 1800-01" in exc_info.value.detail


class TestGetCalendarYearService:
    def test_returns_tibetan_year_grouped_by_lunar_month(self):
        result = get_calendar_year_service(2025)

        assert result.year == 2025
        assert result.new_year is not None
        assert result.new_year.year == "2025"
        assert "1" in result.months
        assert result.months["1"].days[0].lunar_month.month == 1

    def test_raises_for_invalid_tibetan_year(self):
        with pytest.raises(HTTPException) as exc_info:
            get_calendar_year_service(1700)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "Calendar year 1700" in exc_info.value.detail

    def test_raises_when_calendar_file_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "pecha_api.calendar.calendar_parser.PHUGPA_CALENDAR_DIR",
            tmp_path,
        )
        with pytest.raises(HTTPException) as exc_info:
            get_calendar_year_service(2025)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "No calendar file for year 2025" in exc_info.value.detail


class TestGetCalendarTodayService:
    def test_returns_today_calendar_day(self):
        sample_day = {
            "gregorian_date": "2025-03-15",
            "lunar_day": 16,
            "lunar_month": {"month": 1, "designation": "Earth-male-Dragon"},
            "new_year": {"year": "2025", "designation": "Wood-female-Snake"},
            "day_summary": "sample day",
        }

        with patch(
            "pecha_api.calendar.calendar_service.find_calendar_day_for_gregorian_date",
            return_value=(2025, sample_day),
        ):
            result = get_calendar_today_service()

        assert result.tibetan_year == 2025
        assert result.day.lunar_day == 16
        assert result.gregorian_date == date.today()

    def test_raises_when_today_not_found(self):
        with patch(
            "pecha_api.calendar.calendar_service.find_calendar_day_for_gregorian_date",
            return_value=None,
        ):
            with pytest.raises(HTTPException) as exc_info:
                get_calendar_today_service()

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "No calendar data found for" in exc_info.value.detail
