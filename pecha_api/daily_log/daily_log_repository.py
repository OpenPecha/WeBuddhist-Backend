from datetime import date, timedelta
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from pecha_api.daily_log.daily_log_models import UserDailyLog

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


def get_week_active_days(db: Session, user_id: UUID, today: date) -> int:
    """Count distinct days the user logged within the trailing 7 days (0-7)."""
    week_start = today - timedelta(days=6)
    return db.query(UserDailyLog.log_date).filter(
        UserDailyLog.user_id == user_id,
        UserDailyLog.log_date >= week_start,
        UserDailyLog.log_date <= today,
    ).distinct().count()


def get_highest_streak(db: Session, user_id: UUID) -> int:
    """Longest run of consecutive daily logs across the user's full history."""
    log_dates = sorted(
        row.log_date
        for row in db.query(UserDailyLog.log_date).filter(
            UserDailyLog.user_id == user_id,
        ).all()
    )

    if not log_dates:
        return 0

    highest = 1
    current = 1
    for previous, current_date in zip(log_dates, log_dates[1:]):
        if current_date == previous + timedelta(days=1):
            current += 1
        elif current_date != previous:
            current = 1
        highest = max(highest, current)

    return highest


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
