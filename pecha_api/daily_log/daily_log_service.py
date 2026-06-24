from datetime import date, datetime, timedelta, timezone
from typing import Set
from uuid import UUID

from sqlalchemy.orm import Session

from pecha_api.db.database import SessionLocal
from pecha_api.daily_log.daily_log_cache_service import (
    get_user_stats_cache,
    invalidate_user_stats_cache,
    is_user_logged_today_in_cache,
    set_user_daily_log_cache,
    set_user_stats_cache,
)
from pecha_api.daily_log.daily_log_repository import (
    get_highest_streak,
    get_user_activity_totals,
    get_user_streak,
    get_week_active_days,
    has_log_for_date,
    save_daily_log,
)
from pecha_api.daily_log.daily_log_response_models import (
    StreakStats,
    UserStatsResponse,
    UserStreakResponse,
)
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


async def record_daily_log_if_needed(user_id: UUID, db: Session | None = None) -> None:
    today = _utc_today()

    if await is_user_logged_today_in_cache(user_id=user_id, log_date=today):
        return

    if db is not None:
        if has_log_for_date(db=db, user_id=user_id, log_date=today):
            await set_user_daily_log_cache(user_id=user_id, log_date=today)
            return

        save_daily_log(db=db, user_id=user_id, log_date=today)
        await set_user_daily_log_cache(user_id=user_id, log_date=today)
        await invalidate_user_stats_cache(user_id=user_id)
        return

    with SessionLocal() as session:
        if has_log_for_date(db=session, user_id=user_id, log_date=today):
            await set_user_daily_log_cache(user_id=user_id, log_date=today)
            return

        save_daily_log(db=session, user_id=user_id, log_date=today)

    await set_user_daily_log_cache(user_id=user_id, log_date=today)
    await invalidate_user_stats_cache(user_id=user_id)


async def get_user_streak_service(token: str) -> UserStreakResponse:
    current_user = validate_and_extract_user_details(token=token)
    today = _utc_today()

    await record_daily_log_if_needed(user_id=current_user.id)

    with SessionLocal() as db:
        streak = get_user_streak(db=db, user_id=current_user.id, today=today)

    return UserStreakResponse(streak=streak)


async def get_user_stats_service(token: str) -> UserStatsResponse:
    current_user = validate_and_extract_user_details(token=token)
    today = _utc_today()

    user_id = current_user.id
    with SessionLocal() as db:
        await record_daily_log_if_needed(user_id=user_id, db=db)

        cached_stats = await get_user_stats_cache(user_id=user_id)
        if cached_stats is not None:
            return cached_stats

        current_streak = get_user_streak(db=db, user_id=user_id, today=today)
        highest_streak = get_highest_streak(db=db, user_id=user_id)
        week_active_days = get_week_active_days(db=db, user_id=user_id, today=today)
        total_timer, total_accumulated, total_practice_days = get_user_activity_totals(
            db=db,
            user_id=user_id,
        )

    stats = UserStatsResponse(
        streak=StreakStats(
            current=current_streak,
            highest=highest_streak,
            week=week_active_days,
        ),
        total_timer=total_timer,
        total_accumulated=total_accumulated,
        total_practice_days=total_practice_days,
    )
    await set_user_stats_cache(user_id=user_id, data=stats)
    return stats
