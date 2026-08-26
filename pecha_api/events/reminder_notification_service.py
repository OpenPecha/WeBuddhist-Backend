from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session
from starlette import status

from pecha_api.chat.notification_repository import (
    get_active_push_devices_by_user_ids,
    normalize_platform,
)
from pecha_api.db.database import SessionLocal
from pecha_api.events.event_metadata_model import EventMetadata
from pecha_api.events.event_participant_repository import get_event_participants_paginated
from pecha_api.events.event_reminder_repository import get_event_reminder
from pecha_api.events.event_repository import get_event_by_id
from pecha_api.events.event_reminder_service import REMINDER_TYPE_T_MINUS_10, REMINDER_TYPE_T_ZERO
from pecha_api.events.notification_response_models import (
    EventNotificationRecipientDTO,
    EventPushDeviceTargetDTO,
    EventReminderTargetsResponse,
)
from pecha_api.plans.response_message import NOT_FOUND

_REMINDER_COPY = {
    REMINDER_TYPE_T_MINUS_10: "Starting in {minutes} minutes",
    REMINDER_TYPE_T_ZERO: "Starting now",
}


def _get_event_name(db: Session, event_id: UUID) -> str:
    entries = (
        db.query(EventMetadata)
        .filter(EventMetadata.event_id == event_id)
        .all()
    )
    for entry in entries:
        language = entry.language
        lang_value = language.value if hasattr(language, "value") else str(language)
        if lang_value.upper() == "EN":
            return entry.name
    if entries:
        return entries[0].name
    return "Your event"


def _build_reminder_copy(*, reminder_type: str, event_name: str, minutes_before: int) -> str:
    template = _REMINDER_COPY.get(reminder_type, "Starting now")
    return template.format(minutes=minutes_before)


def _reminder_superseded(db: Session, event_id: UUID, reminder_type: str) -> bool:
    """Final check right before targets are handed back for actual push
    delivery - the closest point in the pipeline to real publication, and
    the last chance to catch a cancellation or reschedule that committed
    after the dispatcher's own best-effort pre-send check (see
    event_reminder_dispatch_service._reminder_still_due) already passed. A
    canceled row means delivery must be suppressed outright; a fire_at now
    in the future means a reschedule's upsert overwrote this row after it
    was claimed - a legitimately due row always has fire_at <= now, so a
    future fire_at can only mean this claim targets a schedule that no
    longer holds."""
    reminder = get_event_reminder(db, event_id, reminder_type)
    if reminder is None or reminder.canceled_at is not None:
        return True
    return reminder.fire_at > datetime.now(timezone.utc)


def get_event_reminder_targets(
    *,
    event_id: UUID,
    reminder_type: str,
    minutes_before: int,
    skip: int = 0,
    limit: int = 100,
) -> EventReminderTargetsResponse:
    if skip < 0:
        skip = 0
    if limit < 1:
        limit = 1
    if limit > 500:
        limit = 500

    with SessionLocal() as db:
        event = get_event_by_id(db, event_id)
        if not event:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NOT_FOUND)

        if _reminder_superseded(db, event_id, reminder_type):
            return EventReminderTargetsResponse(
                event_id=event.id,
                reminder_type=reminder_type,
                title="",
                body="",
                recipients=[],
                skip=skip,
                limit=limit,
                total=0,
                has_more=False,
            )

        event_name = _get_event_name(db, event.id)
        title = event_name
        body = _build_reminder_copy(
            reminder_type=reminder_type,
            event_name=event_name,
            minutes_before=minutes_before,
        )

        participant_rows, total = get_event_participants_paginated(
            db=db, event_id=event_id, skip=skip, limit=limit,
        )
        recipient_ids = [user.id for user, _ in participant_rows]

        devices_by_user = get_active_push_devices_by_user_ids(db=db, user_ids=recipient_ids)
        recipients: list[EventNotificationRecipientDTO] = []
        for user_id in recipient_ids:
            devices = devices_by_user.get(user_id) or []
            if not devices:
                continue
            recipients.append(
                EventNotificationRecipientDTO(
                    user_id=user_id,
                    push_devices=[
                        EventPushDeviceTargetDTO(
                            id=device.id,
                            token=device.token,
                            platform=normalize_platform(device.platform),
                        )
                        for device in devices
                    ],
                )
            )

        return EventReminderTargetsResponse(
            event_id=event.id,
            reminder_type=reminder_type,
            title=title,
            body=body,
            recipients=recipients,
            skip=skip,
            limit=limit,
            total=total,
            has_more=(skip + limit) < total,
        )
