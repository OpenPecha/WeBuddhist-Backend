from datetime import date
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from starlette import status

from pecha_api.app import api
from pecha_api.calendar.calendar_parser import CalendarType
from pecha_api.calendar.calendar_response_models import (
    CalendarDay,
    CalendarMonthResponse,
    CalendarTodayResponse,
    CalendarYearResponse,
    LunarMonthInfo,
    NewYearInfo,
)

client = TestClient(api)


@pytest.fixture(autouse=True)
def mock_calendar_cache():
    with (
        patch(
            "pecha_api.calendar.calendar_service.get_calendar_year_cache",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "pecha_api.calendar.calendar_service.set_calendar_year_cache",
            new_callable=AsyncMock,
            return_value=True,
        ),
    ):
        yield


class TestCalendarViewEndpoint:
    def test_get_calendar_view_returns_html(self):
        response = client.get("/calendar/view")

        assert response.status_code == status.HTTP_200_OK
        assert "text/html" in response.headers["content-type"]
        assert "<html" in response.text.lower()
        assert 'id="calendar-type-select"' in response.text
        assert '<option value="tsurphu">Tsurphu</option>' in response.text


class TestCalendarTypesEndpoint:
    def test_get_available_calendar_types(self):
        response = client.get("/calendar/types")

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == ["phugpa", "tsurphu"]


class TestCalendarTodayEndpoint:
    def test_get_calendar_today_success(self):
        today_response = CalendarTodayResponse(
            gregorian_date=date(2025, 3, 15),
            tibetan_year=2152,
            day=CalendarDay(
                gregorian_date="2025-03-15",
                lunar_day=16,
                lunar_month=LunarMonthInfo(month=1, designation="Earth-male-Dragon"),
                day_summary="sample day",
            ),
        )

        with patch(
            "pecha_api.calendar.calendar_views.get_calendar_today_service",
            new_callable=AsyncMock,
            return_value=today_response,
        ) as get_today:
            response = client.get("/calendar/today")

        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert body["tibetan_year"] == 2152
        assert body["day"]["lunar_day"] == 16
        get_today.assert_awaited_once_with(CalendarType.PHUGPA)


class TestCalendarYearEndpoint:
    def test_get_calendar_year_success(self):
        year_response = CalendarYearResponse(
            year=2025,
            tibetan_year=2152,
            new_year=NewYearInfo(year="2152", designation="Wood-female-Snake"),
            months={},
        )

        with patch(
            "pecha_api.calendar.calendar_views.get_calendar_year_service",
            new_callable=AsyncMock,
            return_value=year_response,
        ) as get_year:
            response = client.get("/calendar/2025?calendar_type=tsurphu")

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["year"] == 2025
        get_year.assert_awaited_once_with(2025, CalendarType.TSURPHU)

    def test_rejects_unknown_calendar_type(self):
        response = client.get("/calendar/2025?calendar_type=unknown")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestCalendarMonthEndpoint:
    def test_get_calendar_month_success(self):
        month_response = CalendarMonthResponse(
            year=2025,
            month=3,
            days=[
                CalendarDay(
                    gregorian_date="2025-03-01",
                    lunar_day=2,
                    lunar_month=LunarMonthInfo(month=1, designation="Earth-male-Dragon"),
                    day_summary="sample day",
                )
            ],
        )

        with patch(
            "pecha_api.calendar.calendar_views.get_calendar_month_service",
            new_callable=AsyncMock,
            return_value=month_response,
        ) as get_month:
            response = client.get("/calendar/2025/3")

        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert body["year"] == 2025
        assert body["month"] == 3
        assert len(body["days"]) == 1
        get_month.assert_awaited_once_with(2025, 3, CalendarType.PHUGPA)

    def test_get_calendar_month_integration(self):
        response = client.get("/calendar/2025/3")

        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert body["year"] == 2025
        assert body["month"] == 3
        assert len(body["days"]) == 31

    def test_get_tsurphu_calendar_month_integration(self):
        response = client.get("/calendar/2025/3?calendar_type=tsurphu")

        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert len(body["days"]) == 31
        assert body["days"][0]["lunar_month"]["designation"] == "Earth-male-Tiger"
