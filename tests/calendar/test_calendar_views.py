from datetime import date
from unittest.mock import patch

from fastapi.testclient import TestClient
from starlette import status

from pecha_api.app import api
from pecha_api.calendar.calendar_response_models import (
    CalendarDay,
    CalendarMonthResponse,
    CalendarTodayResponse,
    CalendarYearResponse,
    LunarMonthInfo,
    NewYearInfo,
)

client = TestClient(api)


class TestCalendarViewEndpoint:
    def test_get_calendar_view_returns_html(self):
        response = client.get("/calendar/view")

        assert response.status_code == status.HTTP_200_OK
        assert "text/html" in response.headers["content-type"]
        assert "<html" in response.text.lower()


class TestCalendarTodayEndpoint:
    def test_get_calendar_today_success(self):
        today_response = CalendarTodayResponse(
            gregorian_date=date(2025, 3, 15),
            tibetan_year=2025,
            day=CalendarDay(
                gregorian_date="2025-03-15",
                lunar_day=16,
                lunar_month=LunarMonthInfo(month=1, designation="Earth-male-Dragon"),
                day_summary="sample day",
            ),
        )

        with patch(
            "pecha_api.calendar.calendar_views.get_calendar_today_service",
            return_value=today_response,
        ):
            response = client.get("/calendar/today")

        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert body["tibetan_year"] == 2025
        assert body["day"]["lunar_day"] == 16


class TestCalendarYearEndpoint:
    def test_get_calendar_year_success(self):
        year_response = CalendarYearResponse(
            year=2025,
            new_year=NewYearInfo(year="2025", designation="Wood-female-Snake"),
            months={},
        )

        with patch(
            "pecha_api.calendar.calendar_views.get_calendar_year_service",
            return_value=year_response,
        ):
            response = client.get("/calendar/2025")

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["year"] == 2025


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
            return_value=month_response,
        ):
            response = client.get("/calendar/2025/3")

        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert body["year"] == 2025
        assert body["month"] == 3
        assert len(body["days"]) == 1

    def test_get_calendar_month_integration(self):
        response = client.get("/calendar/2025/3")

        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert body["year"] == 2025
        assert body["month"] == 3
        assert len(body["days"]) == 31
