from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse
from starlette import status

from .calendar_parser import CalendarType
from .calendar_response_models import (
    CalendarMonthResponse,
    CalendarTodayResponse,
    CalendarYearResponse,
)
from .calendar_service import (
    get_calendar_month_service,
    get_calendar_today_service,
    get_calendar_year_service,
)

calendar_router = APIRouter(
    prefix="/calendar",
    tags=["Calendar"],
)

_CALENDAR_HTML = Path(__file__).resolve().parent / "static" / "calendar.html"


@calendar_router.get(
    "/view",
    include_in_schema=False,
)
def get_calendar_view() -> FileResponse:
    return FileResponse(_CALENDAR_HTML, media_type="text/html")


@calendar_router.get(
    "/today",
    status_code=status.HTTP_200_OK,
    response_model=CalendarTodayResponse,
)
async def get_calendar_today_endpoint(
    calendar_type: CalendarType = CalendarType.PHUGPA,
) -> CalendarTodayResponse:
    return await get_calendar_today_service(calendar_type)


@calendar_router.get(
    "/types",
    status_code=status.HTTP_200_OK,
    response_model=list[CalendarType],
)
def get_available_calendar_types_endpoint() -> list[CalendarType]:
    return list(CalendarType)


@calendar_router.get(
    "/{year}",
    status_code=status.HTTP_200_OK,
    response_model=CalendarYearResponse,
)
async def get_calendar_year_endpoint(
    year: int,
    calendar_type: CalendarType = CalendarType.PHUGPA,
) -> CalendarYearResponse:
    return await get_calendar_year_service(year, calendar_type)


@calendar_router.get(
    "/{year}/{month}",
    status_code=status.HTTP_200_OK,
    response_model=CalendarMonthResponse,
)
async def get_calendar_month_endpoint(
    year: int,
    month: int,
    calendar_type: CalendarType = CalendarType.PHUGPA,
) -> CalendarMonthResponse:
    return await get_calendar_month_service(year, month, calendar_type)
