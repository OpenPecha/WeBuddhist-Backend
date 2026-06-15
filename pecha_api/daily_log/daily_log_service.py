from datetime import date, datetime, timedelta, timezone
from typing import Set
from uuid import UUID

from pecha_api.db.database import SessionLocal
from pecha_api.daily_log.daily_log_cache_service import (
    is_user_logged_today_in_cache,
    set_user_daily_log_cache,
)
from pecha_api.daily_log.daily_log_repository import (
    get_user_streak,
    has_log_for_date,
    save_daily_log,
)
from pecha_api.daily_log.daily_log_response_models import UserStreakResponse
from pecha_api.users.users_service import validate_and_extract_user_details


def _utc_today() -> date:
    return datetime.now(timezone.utc).date()


def calculate_streak(log_dates: Set[date]) -> int:
    today = _utc_today()
    yesterday = today - timedelta(days=1)

    if today not in log_dates and yesterday not in log_dates:
        return 0

    anchor = today if today in log_dates else yesterday
    streak = 0
    current = anchor
    while current in log_dates:
        streak += 1
        current -= timedelta(days=1)

    return streak


async def register_daily_log_service(token: str) -> None:
    current_user = validate_and_extract_user_details(token=token)
    await record_daily_log_if_needed(user_id=current_user.id)


async def record_daily_log_if_needed(user_id: UUID) -> None:
    today = _utc_today()

    if await is_user_logged_today_in_cache(user_id=user_id, log_date=today):
        return

    with SessionLocal() as db:
        if has_log_for_date(db=db, user_id=user_id, log_date=today):
            await set_user_daily_log_cache(user_id=user_id, log_date=today)
            return

        save_daily_log(db=db, user_id=user_id, log_date=today)

    await set_user_daily_log_cache(user_id=user_id, log_date=today)


async def get_user_streak_service(token: str) -> UserStreakResponse:
    current_user = validate_and_extract_user_details(token=token)
    today = _utc_today()

    with SessionLocal() as db:
        streak = get_user_streak(db=db, user_id=current_user.id, today=today)

    return UserStreakResponse(streak=streak)
