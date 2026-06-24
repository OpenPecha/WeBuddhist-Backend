from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import Integer, cast, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from pecha_api.accumulator.accumulator_history_model import AccumulatorHistory
from pecha_api.daily_log.daily_log_models import UserDailyLog
from pecha_api.plans.users.plan_users_models import UserDayCompletion
from pecha_api.timers.timer_history_model import TimerHistory

_STREAK_CHUNK_SIZE = 32


def has_log_for_date(db: Session, user_id: UUID, log_date: date) -> bool:
    return db.query(UserDailyLog.id).filter(
        UserDailyLog.user_id == user_id,
        UserDailyLog.log_date == log_date,
    ).first() is not None


def save_daily_log(db: Session, user_id: UUID, log_date: date) -> None:
    try:
        daily_log = UserDailyLog(user_id=user_id, log_date=log_date)
        db.add(daily_log)
        db.commit()
        db.refresh(daily_log)
    except IntegrityError:
        db.rollback()


def get_week_active_days(db: Session, user_id: UUID, today: date) -> list[int]:
    """Which days the user was active this week, as a list like [2, 3, 6]
    (Mon=1 .. Sun=7). The week runs Monday to Sunday."""
    week_start = today - timedelta(days=today.weekday())
    rows = db.query(UserDailyLog.log_date).filter(
        UserDailyLog.user_id == user_id,
        UserDailyLog.log_date >= week_start,
        UserDailyLog.log_date <= today,
    ).distinct().all()
    return sorted(row.log_date.isoweekday() for row in rows)


def get_highest_streak(db: Session, user_id: UUID) -> int:
    """Longest run of consecutive daily logs across the user's full history."""
    row_number = func.row_number().over(order_by=UserDailyLog.log_date)
    streak_group = (UserDailyLog.log_date - cast(row_number, Integer)).label("grp")

    grouped = (
        select(streak_group)
        .where(UserDailyLog.user_id == user_id)
        .subquery()
    )
    streak_lengths = (
        select(func.count().label("streak_length"))
        .select_from(grouped)
        .group_by(grouped.c.grp)
        .subquery()
    )

    result = db.execute(
        select(func.coalesce(func.max(streak_lengths.c.streak_length), 0))
    ).scalar_one()

    return int(result)


def get_user_activity_totals(db: Session, user_id: UUID) -> tuple[int, int, int]:
    """Timer ms, accumulated count, and completed plan days in one round trip."""
    timer_total = (
        select(func.coalesce(func.sum(TimerHistory.duration_ms), 0))
        .where(TimerHistory.user_id == user_id)
        .scalar_subquery()
    )
    accumulated_total = (
        select(func.coalesce(func.sum(AccumulatorHistory.count), 0))
        .where(AccumulatorHistory.user_id == user_id)
        .scalar_subquery()
    )
    practice_days_total = (
        select(func.coalesce(func.count(UserDayCompletion.id), 0))
        .where(UserDayCompletion.user_id == user_id)
        .scalar_subquery()
    )

    row = db.execute(
        select(timer_total, accumulated_total, practice_days_total)
    ).one()

    return int(row[0]), int(row[1]), int(row[2])


def get_user_streak(db: Session, user_id: UUID, today: date) -> int:
    """Count consecutive daily logs ending today or yesterday without loading full history."""
    yesterday = today - timedelta(days=1)
    recent_dates = {
        row.log_date
        for row in db.query(UserDailyLog.log_date).filter(
            UserDailyLog.user_id == user_id,
            UserDailyLog.log_date.in_([today, yesterday]),
        ).all()
    }

    if today not in recent_dates and yesterday not in recent_dates:
        return 0

    anchor = today if today in recent_dates else yesterday
    streak = 0
    chunk_end = anchor

    while True:
        chunk_start = chunk_end - timedelta(days=_STREAK_CHUNK_SIZE - 1)
        chunk_dates = {
            row.log_date
            for row in db.query(UserDailyLog.log_date).filter(
                UserDailyLog.user_id == user_id,
                UserDailyLog.log_date >= chunk_start,
                UserDailyLog.log_date <= chunk_end,
            ).all()
        }

        current = chunk_end
        while current >= chunk_start:
            if current not in chunk_dates:
                return streak
            streak += 1
            current -= timedelta(days=1)

        chunk_end = chunk_start - timedelta(days=1)
