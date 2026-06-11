from datetime import date
from typing import Set
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from pecha_api.daily_log.daily_log_models import UserDailyLog


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


def get_user_log_dates(db: Session, user_id: UUID) -> Set[date]:
    rows = db.query(UserDailyLog.log_date).filter(
        UserDailyLog.user_id == user_id,
    ).all()
    return {row.log_date for row in rows}
