from dataclasses import dataclass
from datetime import datetime, time
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from pecha_api.plans.items.plan_items_models import PlanItem
from pecha_api.plans.notifications.day_notification_models import DayNotification
from pecha_api.plans.notifications.day_notification_repository import get_notification_by_day_id
from pecha_api.plans.plans_models import Plan
from pecha_api.plans.series.series_metadata_model import SeriesMetadata
from pecha_api.plans.series.series_model import Series
from pecha_api.plans.users.plan_users_models import UserPlanProgress
from pecha_api.plans.users.recitation_collection.recitation_collection_models import RecitationCollection
from pecha_api.push_devices.push_device_models import PushDeviceToken
from pecha_api.routines.routines_models import Routine, RoutineSession, RoutineTimeBlock


@dataclass(frozen=True)
class RoutineNotificationRow:
    user_id: UUID
    time_block_id: UUID
    session_type: str
    source_id: UUID | None
    device_token: str
    platform: str
    time_block_time_utc: time


def get_users_with_matching_timeblocks(db: Session) -> list[RoutineNotificationRow]:
    stmt = (
        select(
            Routine.user_id,
            RoutineTimeBlock.id,
            RoutineTimeBlock.time_utc,
            RoutineSession.session_type,
            RoutineSession.source_id,
            PushDeviceToken.token,
            PushDeviceToken.platform,
        )
        .join(Routine, RoutineTimeBlock.routine_id == Routine.id)
        .join(RoutineSession, RoutineSession.time_block_id == RoutineTimeBlock.id)
        .join(PushDeviceToken, PushDeviceToken.user_id == Routine.user_id)
        .where(
            RoutineTimeBlock.notification_enabled.is_(True),
            RoutineTimeBlock.deleted_at.is_(None),
            Routine.deleted_at.is_(None),
            PushDeviceToken.is_active.is_(True),
        )
    )

    rows = db.execute(stmt).all()
    return [
        RoutineNotificationRow(
            user_id=row.user_id,
            time_block_id=row.id,
            time_block_time_utc=row.time_utc,
            session_type=str(row.session_type),
            source_id=row.source_id,
            device_token=row.token,
            platform=str(row.platform).lower(),
        )
        for row in rows
    ]


def get_plan_by_id(db: Session, plan_id: UUID) -> Plan | None:
    return db.get(Plan, plan_id)


def get_series_by_id(db: Session, series_id: UUID) -> Series | None:
    return db.get(Series, series_id)


def get_series_metadata(db: Session, series_id: UUID) -> SeriesMetadata | None:
    stmt = (
        select(SeriesMetadata)
        .where(SeriesMetadata.series_id == series_id)
        .limit(1)
    )
    return db.scalars(stmt).first()


def get_user_plan_progress(db: Session, *, user_id: UUID, plan_id: UUID) -> UserPlanProgress | None:
    stmt = select(UserPlanProgress).where(
        UserPlanProgress.user_id == user_id,
        UserPlanProgress.plan_id == plan_id,
    )
    return db.scalars(stmt).first()


def get_plan_item_by_day_number(db: Session, *, plan_id: UUID, day_number: int) -> PlanItem | None:
    stmt = select(PlanItem).where(
        PlanItem.plan_id == plan_id,
        PlanItem.day_number == day_number,
    )
    return db.scalars(stmt).first()


def get_day_notification(db: Session, *, day_id: UUID) -> DayNotification | None:
    return get_notification_by_day_id(db=db, day_id=day_id)


def get_recitation_collection(db: Session, collection_id: UUID) -> RecitationCollection | None:
    return db.get(RecitationCollection, collection_id)
