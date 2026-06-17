from datetime import date
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from starlette import status

from .calendar_parser import (
    MAX_CALENDAR_YEAR,
    MIN_CALENDAR_YEAR,
    find_calendar_day_for_gregorian_date,
    get_days_for_gregorian_month,
    parse_calendar_year,
)
from .calendar_response_models import (
    CalendarDay,
    CalendarMonthData,
    CalendarMonthResponse,
    CalendarTodayResponse,
    CalendarYearResponse,
    LunarMonthInfo,
    NewYearInfo,
    SolarInfo,
)


def _to_calendar_day(day_data: Dict[str, Any]) -> CalendarDay:
    lunar_month = day_data.get("lunar_month")
    new_year = day_data.get("new_year")
    solar = day_data.get("solar")

    return CalendarDay(
        gregorian_date=day_data.get("gregorian_date"),
        lunar_day=day_data["lunar_day"],
        lunar_month=LunarMonthInfo(**lunar_month) if lunar_month else None,
        new_year=NewYearInfo(**new_year) if new_year else None,
        day_summary=day_data["day_summary"],
        lunar_qualities=day_data.get("lunar_qualities"),
        lunar_times=day_data.get("lunar_times"),
        solar=SolarInfo(**solar) if solar else None,
    )


def _validate_year(year: int) -> None:
    if year < MIN_CALENDAR_YEAR or year > MAX_CALENDAR_YEAR:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Calendar year {year} is not available. "
            f"Supported range: {MIN_CALENDAR_YEAR}-{MAX_CALENDAR_YEAR}.",
        )


MIN_GREGORIAN_YEAR = MIN_CALENDAR_YEAR
MAX_GREGORIAN_YEAR = MAX_CALENDAR_YEAR + 1


def _validate_gregorian_year(year: int) -> None:
    if year < MIN_GREGORIAN_YEAR or year > MAX_GREGORIAN_YEAR:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Gregorian year {year} is not available. "
            f"Supported range: {MIN_GREGORIAN_YEAR}-{MAX_GREGORIAN_YEAR}.",
        )


def _validate_gregorian_month(month: int) -> None:
    if month < 1 or month > 12:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Month must be between 1 and 12.",
        )


def _group_days_by_month(year_data: Dict[str, Dict[str, Any]]) -> Dict[int, List[CalendarDay]]:
    months: Dict[int, List[CalendarDay]] = {}
    for day_data in year_data.values():
        lunar_month = day_data.get("lunar_month")
        if not lunar_month:
            continue
        month_number = lunar_month["month"]
        months.setdefault(month_number, []).append(_to_calendar_day(day_data))

    for month_days in months.values():
        month_days.sort(
            key=lambda day: (
                day.gregorian_date is None,
                day.gregorian_date or "",
                day.lunar_day,
            )
        )
    return months


def get_calendar_today_service() -> CalendarTodayResponse:
    today = date.today()
    result = find_calendar_day_for_gregorian_date(today)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No calendar data found for {today.isoformat()}.",
        )

    tibetan_year, day_data = result
    return CalendarTodayResponse(
        gregorian_date=today,
        tibetan_year=tibetan_year,
        day=_to_calendar_day(day_data),
    )


def get_calendar_year_service(year: int) -> CalendarYearResponse:
    _validate_year(year)
    try:
        year_data = parse_calendar_year(year)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    grouped_months = _group_days_by_month(year_data)
    new_year_info: Optional[NewYearInfo] = None
    for day_data in year_data.values():
        if day_data.get("new_year"):
            new_year_info = NewYearInfo(**day_data["new_year"])
            break

    months = {
        str(month_number): CalendarMonthData(
            month=month_number,
            designation=days[0].lunar_month.designation if days[0].lunar_month else None,
            days=days,
        )
        for month_number, days in sorted(grouped_months.items())
    }

    return CalendarYearResponse(year=year, new_year=new_year_info, months=months)


def get_calendar_month_service(year: int, month: int) -> CalendarMonthResponse:
    _validate_gregorian_year(year)
    _validate_gregorian_month(month)

    month_days_data = get_days_for_gregorian_month(year, month)
    if not month_days_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No calendar data found for {year}-{month:02d}.",
        )

    month_days = [_to_calendar_day(day_data) for day_data in month_days_data]
    return CalendarMonthResponse(
        year=year,
        month=month,
        designation=None,
        days=month_days,
    )
