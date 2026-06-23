from datetime import date, datetime, time, timezone
from typing import Optional, Tuple, Union
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

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
    try:
        ZoneInfo(cleaned)
    except ZoneInfoNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid timezone: {timezone_name}",
        ) from exc
    return cleaned


def _resolve_timezone(timezone_name: Optional[str]) -> TimezoneInfo:
    if not timezone_name or not timezone_name.strip():
        return timezone.utc

    try:
        return ZoneInfo(timezone_name.strip())
    except ZoneInfoNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid timezone: {timezone_name}",
        ) from exc
