from __future__ import annotations

from collections import defaultdict
from datetime import datetime, time, timezone
from uuid import UUID

from pecha_api.config import get
from pecha_api.db.database import SessionLocal
from pecha_api.plans.authors.plan_authors_service import safe_get_image_url
from pecha_api.plans.media.media_response_models import ImageUrlModel
from pecha_api.plans.notifications.day_notification_models import DayNotification
from pecha_api.plans.plans_models import Plan
from pecha_api.plans.series.series_model import Series
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
from pecha_api.uploads.S3_utils import generate_presigned_access_url

SESSION_TYPE_PLAN = "PLAN"
SESSION_TYPE_SERIES = "SERIES"
IMAGE_TYPE_PLAN = "PLAN"
IMAGE_TYPE_CUSTOM = "CUSTOM"


def _default_notification_copy() -> tuple[str, str]:
    return get("NOTIFICATION_DEFAULT_TITLE"), get("NOTIFICATION_DEFAULT_BODY")


def _notification_content(
    title: str,
    body: str,
    image_url: str | None = None,
) -> NotificationContentDTO:
    return NotificationContentDTO(title=title, body=body, image_url=image_url)


def _resolve_resource_image_url(
    image_key: str | None,
    *,
    resource_id: UUID,
    resource_type: str,
) -> str | None:
    if not image_key:
        return None
    return _image_model_to_url(
        safe_get_image_url(image_key, resource_id=resource_id, resource_type=resource_type)
    )


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


def _image_model_to_url(image: ImageUrlModel | None) -> str | None:
    if image is None:
        return None
    return image.original or image.medium or image.thumbnail


def _presign_s3_key(s3_key: str | None) -> str | None:
    if not s3_key:
        return None
    try:
        return generate_presigned_access_url(
            bucket_name=get("AWS_BUCKET_NAME"),
            s3_key=s3_key,
        )
    except Exception:
        return None


def _resolve_plan_image_url(plan: Plan | None) -> str | None:
    if plan is None:
        return None
    return _resolve_resource_image_url(
        plan.image_url, resource_id=plan.id, resource_type="plan"
    )


def _resolve_series_image_url(series: Series | None) -> str | None:
    if series is None:
        return None
    return _resolve_resource_image_url(
        series.image, resource_id=series.id, resource_type="series"
    )


def _resolve_day_notification_image_url(
    day_notification: DayNotification,
    plan: Plan | None,
) -> str | None:
    image_type = day_notification.image_type.value if day_notification.image_type else None
    if image_type == IMAGE_TYPE_CUSTOM:
        return _presign_s3_key(day_notification.image_url)
    return _resolve_plan_image_url(plan)


def _resolve_source_image_url(db, session_type: str, source_id: UUID | None) -> str | None:
    if source_id is None:
        return None

    if session_type == SESSION_TYPE_PLAN:
        return _resolve_plan_image_url(repo.get_plan_by_id(db, source_id))

    if session_type == SESSION_TYPE_SERIES:
        return _resolve_series_image_url(repo.get_series_by_id(db, source_id))

    return None


def _resolve_notification_content(
    db,
    *,
    session_type: str,
    source_id: UUID | None,
    user_id: UUID,
    utc_now: datetime,
) -> NotificationContentDTO:
    if session_type == SESSION_TYPE_PLAN and source_id is not None:
        return _resolve_plan_notification(db, user_id=user_id, plan_id=source_id, utc_now=utc_now)

    if session_type == SESSION_TYPE_SERIES and source_id is not None:
        return _resolve_series_notification(db, series_id=source_id)

    default_title, default_body = _default_notification_copy()
    return _notification_content(default_title, default_body)


def _resolve_plan_notification(
    db,
    *,
    user_id: UUID,
    plan_id: UUID,
    utc_now: datetime,
) -> NotificationContentDTO:
    default_title, default_body = _default_notification_copy()

    plan = repo.get_plan_by_id(db, plan_id)
    default_content = _notification_content(
        plan.title if plan else default_title,
        default_body,
        _resolve_plan_image_url(plan),
    )

    day_number = _compute_current_day_number(
        repo.get_user_plan_progress(db, user_id=user_id, plan_id=plan_id),
        utc_now,
    )
    plan_item = repo.get_plan_item_by_day_number(db, plan_id=plan_id, day_number=day_number)
    if plan_item is None:
        return default_content

    day_notification = repo.get_day_notification(db, day_id=plan_item.id)
    if day_notification is None:
        return default_content

    return _notification_content(
        day_notification.title,
        day_notification.body,
        _resolve_day_notification_image_url(day_notification, plan),
    )


def _resolve_series_notification(db, *, series_id: UUID) -> NotificationContentDTO:
    default_title, default_body = _default_notification_copy()
    series = repo.get_series_by_id(db, series_id)
    metadata = repo.get_series_metadata(db, series_id)

    return _notification_content(
        metadata.title if metadata else default_title,
        default_body,
        _resolve_series_image_url(series),
    )


def _compute_current_day_number(progress, utc_now: datetime) -> int:
    if progress is None or progress.started_at is None:
        return 1

    started_at = progress.started_at
    if started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=timezone.utc)

    started_date = started_at.date()
    utc_today = utc_now.date()
    return max(1, (utc_today - started_date).days + 1)
