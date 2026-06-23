from datetime import date, datetime, timezone
from typing import Optional, Union
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
