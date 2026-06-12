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

    if yesterday not in recent_dates:
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
