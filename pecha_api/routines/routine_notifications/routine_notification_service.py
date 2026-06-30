from __future__ import annotations

from collections import defaultdict
from datetime import datetime, time, timezone
from uuid import UUID

from pecha_api.config import get
from pecha_api.db.database import SessionLocal
from pecha_api.routines.routine_notifications import routine_notification_repository as repo
from pecha_api.routines.routine_notifications.routine_notification_repository import (
    RoutineNotificationRow,
)
from pecha_api.routines.routine_notifications.routine_notification_response_models import (
    NotificationContentDTO,
    PushDeviceTargetDTO,
    RoutineNotificationGroupDTO,
    RoutineNotificationTargetsResponse,
    RoutineNotificationUserTargetDTO,
)
from pecha_api.timezone_utils import utc_time_to_hhmm

SESSION_TYPE_PLAN = "PLAN"
SESSION_TYPE_SERIES = "SERIES"
SESSION_TYPE_RECITATION = "RECITATION"
SESSION_TYPE_RECITATION_COLLECTION = "RECITATION_COLLECTION"
SESSION_TYPE_ACCUMULATION = "ACCUMULATION"
SESSION_TYPE_TIMER = "TIMER"
IMAGE_TYPE_CUSTOM = "CUSTOM"


def get_routine_notification_targets() -> RoutineNotificationTargetsResponse:
    utc_now = datetime.now(timezone.utc)
    with SessionLocal() as db:
        rows = repo.get_users_with_matching_timeblocks(db)
        filtered_rows = _filter_by_utc_time(rows, utc_now)
        groups = _build_groups(filtered_rows, db, utc_now)

    return RoutineNotificationTargetsResponse(
        generated_at=utc_now,
        matched_time_utc=utc_now.strftime("%H:%M"),
        groups=groups,
    )


def _filter_by_utc_time(
    rows: list[RoutineNotificationRow],
    utc_now: datetime,
) -> list[RoutineNotificationRow]:
    matched: list[RoutineNotificationRow] = []
    seen: set[tuple] = set()

    for row in rows:
        if not _utc_time_matches(row.time_block_time_utc, utc_now):
            continue

        dedupe_key = (
            row.user_id,
            row.time_block_id,
            row.session_type,
            row.source_id,
            row.device_token,
        )
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        matched.append(row)

    return matched


def _utc_time_matches(time_block_time_utc: time | None, utc_now: datetime) -> bool:
    if time_block_time_utc is None:
        return False
    return utc_time_to_hhmm(time_block_time_utc) == utc_now.strftime("%H:%M")


def _build_groups(
    rows: list[RoutineNotificationRow],
    db,
    utc_now: datetime,
) -> list[RoutineNotificationGroupDTO]:
    grouped_rows: dict[tuple[str, UUID | None], list[RoutineNotificationRow]] = defaultdict(list)
    for row in rows:
        grouped_rows[(row.session_type, row.source_id)].append(row)

    groups: list[RoutineNotificationGroupDTO] = []
    for (session_type, source_id), session_rows in sorted(
        grouped_rows.items(),
        key=lambda item: (item[0][0], str(item[0][1])),
    ):
        source_image_url = _resolve_source_image_url(db, session_type, source_id)
        users = _build_user_targets(db, session_type, source_id, session_rows, utc_now)
        groups.append(
            RoutineNotificationGroupDTO(
                session_type=session_type,
                source_id=source_id,
                source_image_url=source_image_url,
                users=users,
            )
        )

    return groups


def _build_user_targets(
    db,
    session_type: str,
    source_id: UUID | None,
    rows: list[RoutineNotificationRow],
    utc_now: datetime,
) -> list[RoutineNotificationUserTargetDTO]:
    users_by_id: dict[UUID, list[RoutineNotificationRow]] = defaultdict(list)
    for row in rows:
        users_by_id[row.user_id].append(row)

    user_targets: list[RoutineNotificationUserTargetDTO] = []
    for user_id, user_rows in sorted(users_by_id.items(), key=lambda item: str(item[0])):
        notification = _resolve_notification_content(
            db,
            session_type=session_type,
            source_id=source_id,
            user_id=user_id,
            utc_now=utc_now,
        )
        devices = _collect_push_devices(user_rows)
        user_targets.append(
            RoutineNotificationUserTargetDTO(
                user_id=user_id,
                notification=notification,
                push_devices=devices,
            )
        )

    return user_targets


def _collect_push_devices(rows: list[RoutineNotificationRow]) -> list[PushDeviceTargetDTO]:
    devices: list[PushDeviceTargetDTO] = []
    seen_tokens: set[str] = set()
    for row in rows:
        if row.device_token in seen_tokens:
            continue
        seen_tokens.add(row.device_token)
        devices.append(
            PushDeviceTargetDTO(
                token=row.device_token,
                platform=row.platform,
            )
        )
    return devices


def _resolve_source_image_url(db, session_type: str, source_id: UUID | None) -> str | None:
    if source_id is None:
        return None

    if session_type == SESSION_TYPE_PLAN:
        plan = repo.get_plan_by_id(db, source_id)
        return plan.image_url if plan else None

    if session_type == SESSION_TYPE_SERIES:
        series = repo.get_series_by_id(db, source_id)
        return series.image if series else None

    if session_type == SESSION_TYPE_RECITATION_COLLECTION:
        collection = repo.get_recitation_collection(db, source_id)
        return collection.img_url if collection else None

    return None


def _resolve_notification_content(
    db,
    *,
    session_type: str,
    source_id: UUID | None,
    user_id: UUID,
    utc_now: datetime,
) -> NotificationContentDTO:
    default_title = get("NOTIFICATION_DEFAULT_TITLE")
    default_body = get("NOTIFICATION_DEFAULT_BODY")

    if session_type == SESSION_TYPE_PLAN and source_id is not None:
        return _resolve_plan_notification(db, user_id=user_id, plan_id=source_id, utc_now=utc_now)

    if session_type == SESSION_TYPE_SERIES and source_id is not None:
        return _resolve_series_notification(db, series_id=source_id)

    if session_type == SESSION_TYPE_RECITATION_COLLECTION and source_id is not None:
        collection = repo.get_recitation_collection(db, source_id)
        if collection:
            return NotificationContentDTO(
                title=collection.name,
                body=default_body,
                custom_image_url=collection.img_url,
            )

    if session_type in {
        SESSION_TYPE_RECITATION,
        SESSION_TYPE_ACCUMULATION,
        SESSION_TYPE_TIMER,
    }:
        return NotificationContentDTO(
            title=default_title,
            body=default_body,
            custom_image_url=None,
        )

    return NotificationContentDTO(
        title=default_title,
        body=default_body,
        custom_image_url=None,
    )


def _resolve_plan_notification(
    db,
    *,
    user_id: UUID,
    plan_id: UUID,
    utc_now: datetime,
) -> NotificationContentDTO:
    default_title = get("NOTIFICATION_DEFAULT_TITLE")
    default_body = get("NOTIFICATION_DEFAULT_BODY")

    plan = repo.get_plan_by_id(db, plan_id)
    plan_title = plan.title if plan else default_title

    day_number = _compute_current_day_number(
        repo.get_user_plan_progress(db, user_id=user_id, plan_id=plan_id),
        utc_now,
    )
    plan_item = repo.get_plan_item_by_day_number(db, plan_id=plan_id, day_number=day_number)
    if plan_item is None:
        return NotificationContentDTO(title=plan_title, body=default_body, custom_image_url=None)

    day_notification = repo.get_day_notification(db, day_id=plan_item.id)
    if day_notification is None:
        return NotificationContentDTO(title=plan_title, body=default_body, custom_image_url=None)

    custom_image_url = None
    image_type = day_notification.image_type.value if day_notification.image_type else None
    if image_type == IMAGE_TYPE_CUSTOM:
        custom_image_url = day_notification.image_url

    return NotificationContentDTO(
        title=day_notification.title,
        body=day_notification.body,
        custom_image_url=custom_image_url,
    )


def _resolve_series_notification(db, *, series_id: UUID) -> NotificationContentDTO:
    default_body = get("NOTIFICATION_DEFAULT_BODY")
    metadata = repo.get_series_metadata(db, series_id)
    title = metadata.title if metadata else get("NOTIFICATION_DEFAULT_TITLE")
    return NotificationContentDTO(title=title, body=default_body, custom_image_url=None)


def _compute_current_day_number(progress, utc_now: datetime) -> int:
    if progress is None or progress.started_at is None:
        return 1

    started_at = progress.started_at
    if started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=timezone.utc)

    started_date = started_at.date()
    utc_today = utc_now.date()
    return max(1, (utc_today - started_date).days + 1)
