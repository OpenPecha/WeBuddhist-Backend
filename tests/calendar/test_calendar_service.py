from datetime import date
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException
from starlette import status

from pecha_api.calendar.calendar_parser import CalendarType
from pecha_api.calendar.calendar_service import (
    _get_calendar_year_data,
    get_calendar_month_service,
    get_calendar_today_service,
    get_calendar_year_service,
)


@pytest.fixture(autouse=True)
def mock_calendar_cache():
    with (
        patch(
            "pecha_api.calendar.calendar_service.get_calendar_year_cache",
            new_callable=AsyncMock,
            return_value=None,
        ) as get_cache,
        patch(
            "pecha_api.calendar.calendar_service.set_calendar_year_cache",
            new_callable=AsyncMock,
            return_value=True,
        ) as set_cache,
    ):
        yield get_cache, set_cache


class TestGetCalendarMonthService:
    @pytest.mark.asyncio
    async def test_returns_gregorian_month_with_lunar_dates(self):
        result = await get_calendar_month_service(2025, 3)

        assert result.year == 2025
        assert result.month == 3
        assert len(result.days) == 31
        assert result.days[0].gregorian_date == "2025-03-01"
        assert result.days[0].lunar_month is not None

    @pytest.mark.asyncio
    async def test_returns_selected_tsurphu_month(self):
        result = await get_calendar_month_service(2025, 3, CalendarType.TSURPHU)

        assert len(result.days) == 31
        assert result.days[0].lunar_month is not None
        assert result.days[0].lunar_month.designation == "Earth-male-Tiger"

    @pytest.mark.asyncio
    async def test_raises_for_invalid_gregorian_year(self):
        with pytest.raises(HTTPException) as exc_info:
            await get_calendar_month_service(1700, 3)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "Gregorian year 1700" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_raises_for_invalid_gregorian_month(self):
        with pytest.raises(HTTPException) as exc_info:
            await get_calendar_month_service(2025, 13)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "between 1 and 12" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_raises_when_month_has_no_data(self):
        with pytest.raises(HTTPException) as exc_info:
            await get_calendar_month_service(1800, 1)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "No calendar data found for 1800-01" in exc_info.value.detail


class TestGetCalendarYearService:
    @pytest.mark.asyncio
    async def test_returns_tibetan_year_grouped_by_lunar_month(self):
        result = await get_calendar_year_service(2025)

        assert result.year == 2025
        assert result.tibetan_year == 2152
        assert result.new_year is not None
        assert result.new_year.year == "2152"
        assert "1" in result.months
        assert result.months["1"].days[0].lunar_month.month == 1

    @pytest.mark.asyncio
    async def test_returns_selected_tsurphu_year(self):
        result = await get_calendar_year_service(2025, CalendarType.TSURPHU)

        assert result.months["1"].designation == "Earth-male-Tiger"
        assert any(day.gregorian_date is None for day in result.months["1"].days)

    @pytest.mark.asyncio
    async def test_raises_for_invalid_tibetan_year(self):
        with pytest.raises(HTTPException) as exc_info:
            await get_calendar_year_service(1700)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "Calendar year 1700" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_raises_when_calendar_file_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(
            "pecha_api.calendar.calendar_parser.PHUGPA_CALENDAR_DIR",
            tmp_path,
        )
        with pytest.raises(HTTPException) as exc_info:
            await get_calendar_year_service(2025)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "No calendar file for year 2025" in exc_info.value.detail


class TestGetCalendarTodayService:
    @pytest.mark.asyncio
    async def test_returns_today_calendar_day(self):
        sample_day = {
            "gregorian_date": "2025-03-15",
            "lunar_day": 16,
            "lunar_month": {"month": 1, "designation": "Earth-male-Dragon"},
            "new_year": {"year": "2025", "designation": "Wood-female-Snake"},
            "day_summary": "sample day",
        }

        with patch(
            "pecha_api.calendar.calendar_service._find_calendar_day_for_gregorian_date",
            new_callable=AsyncMock,
            return_value=(2025, sample_day),
        ) as find_day:
            result = await get_calendar_today_service(CalendarType.TSURPHU)

        assert result.tibetan_year == 2152
        assert result.day.lunar_day == 16
        assert result.day.new_year is not None
        assert result.day.new_year.year == "2152"
        assert result.gregorian_date == date.today()
        find_day.assert_awaited_once_with(date.today(), CalendarType.TSURPHU)

    @pytest.mark.asyncio
    async def test_raises_when_today_not_found(self):
        with patch(
            "pecha_api.calendar.calendar_service._find_calendar_day_for_gregorian_date",
            new_callable=AsyncMock,
            return_value=None,
        ):
            with pytest.raises(HTTPException) as exc_info:
                await get_calendar_today_service()

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "No calendar data found for" in exc_info.value.detail


class TestCalendarDragonflyCache:
    @pytest.mark.asyncio
    async def test_cache_hit_does_not_parse_file(self, mock_calendar_cache):
        get_cache, set_cache = mock_calendar_cache
        cached_data = {"2025-03-01": {"gregorian_date": "2025-03-01"}}
        get_cache.return_value = cached_data

        with patch(
            "pecha_api.calendar.calendar_service.load_calendar_year"
        ) as load_year:
            result = await _get_calendar_year_data(2025, CalendarType.PHUGPA)

        assert result == cached_data
        load_year.assert_not_called()
        set_cache.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_cache_miss_parses_and_stores_data(self, mock_calendar_cache):
        get_cache, set_cache = mock_calendar_cache
        parsed_data = {"2025-03-01": {"gregorian_date": "2025-03-01"}}

        with patch(
            "pecha_api.calendar.calendar_service.load_calendar_year",
            return_value=parsed_data,
        ) as load_year:
            result = await _get_calendar_year_data(2025, CalendarType.TSURPHU)

        assert result == parsed_data
        get_cache.assert_awaited_once_with(2025, CalendarType.TSURPHU)
        load_year.assert_called_once_with(2025, CalendarType.TSURPHU)
        set_cache.assert_awaited_once_with(
            2025,
            CalendarType.TSURPHU,
            parsed_data,
        )
