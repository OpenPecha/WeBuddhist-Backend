from datetime import date, datetime, time, timezone
from typing import Optional, Tuple, Union
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

UTC = timezone.utc

from fastapi import HTTPException
from starlette import status

TimezoneInfo = Union[ZoneInfo, timezone]


def get_date_in_timezone(
    timezone_name: Optional[str],
    at: Optional[datetime] = None,
) -> date:
    moment = at or datetime.now(timezone.utc)
    tz = _resolve_timezone(timezone_name)
    return moment.astimezone(tz).date()


def get_day_bounds_in_timezone(
    timezone_name: Optional[str],
    at: Optional[datetime] = None,
) -> Tuple[datetime, datetime]:
    moment = at or datetime.now(timezone.utc)
    tz = _resolve_timezone(timezone_name)
    local_date = moment.astimezone(tz).date()
    start = datetime.combine(local_date, time.min, tzinfo=tz)
    end = datetime.combine(local_date, time.max, tzinfo=tz)
    return start, end


def normalize_timezone_name(timezone_name: Optional[str]) -> Optional[str]:
    """Validate an IANA timezone name for storage.
    """
    if not timezone_name or not timezone_name.strip():
        return None

    cleaned = timezone_name.strip()
    if cleaned.upper() == "UTC":
        return "UTC"
    try:
        ZoneInfo(cleaned)
    except ZoneInfoNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid timezone: {timezone_name}",
        ) from exc
    return cleaned


def local_hhmm_to_utc_time(
    local_hhmm: str,
    timezone_name: str,
    *,
    on_date: Optional[date] = None,
) -> time:
    """Convert a local wall-clock HH:MM in the given IANA timezone to UTC time-of-day."""
    reference_date = on_date or datetime.now(UTC).date()
    hour, minute = _parse_hhmm(local_hhmm)
    tz = _resolve_timezone(timezone_name)
    local_dt = datetime.combine(reference_date, time(hour, minute), tzinfo=tz)
    return local_dt.astimezone(UTC).timetz()


def utc_time_to_local_hhmm(
    utc_time_value: time,
    timezone_name: str,
    *,
    on_date: Optional[date] = None,
) -> str:
    """Convert a UTC time-of-day to local HH:MM in the given IANA timezone."""
    reference_date = on_date or datetime.now(UTC).date()
    utc_dt = datetime.combine(
        reference_date,
        utc_time_value.replace(tzinfo=None),
        tzinfo=UTC,
    )
    tz = _resolve_timezone(timezone_name)
    return utc_dt.astimezone(tz).strftime("%H:%M")


def utc_time_to_hhmm(utc_time_value: time) -> str:
    """Format a UTC time-of-day as HH:MM."""
    if utc_time_value.tzinfo is not None:
        normalized = utc_time_value.replace(tzinfo=None)
    else:
        normalized = utc_time_value
    return normalized.strftime("%H:%M")


def hhmm_to_time_int(local_hhmm: str) -> int:
    return int(local_hhmm.replace(":", ""))


def _parse_hhmm(local_hhmm: str) -> Tuple[int, int]:
    hour_str, minute_str = local_hhmm.split(":")
    return int(hour_str), int(minute_str)


def _resolve_timezone(timezone_name: Optional[str]) -> TimezoneInfo:
    if not timezone_name or not timezone_name.strip():
        return timezone.utc

    cleaned = timezone_name.strip()
    if cleaned.upper() == "UTC":
        return UTC
    try:
        return ZoneInfo(cleaned)
    except ZoneInfoNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid timezone: {timezone_name}",
        ) from exc
