from datetime import date
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class LunarMonthInfo(BaseModel):
    month: int
    designation: str


class NewYearInfo(BaseModel):
    year: str
    designation: str


class SolarInfo(BaseModel):
    designation: str
    zodiac: str
    number: Optional[str] = None


class CalendarDay(BaseModel):
    gregorian_date: Optional[str] = None
    lunar_day: int
    lunar_month: Optional[LunarMonthInfo] = None
    new_year: Optional[NewYearInfo] = None
    day_summary: str
    lunar_qualities: Optional[str] = None
    lunar_times: Optional[str] = None
    solar: Optional[SolarInfo] = None


class CalendarTodayResponse(BaseModel):
    gregorian_date: date
    tibetan_year: int
    day: CalendarDay


class CalendarMonthData(BaseModel):
    month: int
    designation: Optional[str] = None
    days: List[CalendarDay]


class CalendarYearResponse(BaseModel):
    year: int = Field(description="Western/Losar year matching the source calendar file")
    tibetan_year: int = Field(description="Traditional Tibetan year number")
    new_year: Optional[NewYearInfo] = None
    months: Dict[str, CalendarMonthData] = Field(
        description="Calendar days grouped by Tibetan lunar month number"
    )


class CalendarMonthResponse(BaseModel):
    year: int = Field(description="Gregorian calendar year")
    month: int = Field(description="Gregorian calendar month (1-12)")
    designation: Optional[str] = Field(
        default=None,
        description="Deprecated; lunar month designation is on each day in `days`",
    )
    days: List[CalendarDay]
