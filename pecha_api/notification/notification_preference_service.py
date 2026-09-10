from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional, Sequence, Tuple
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session
from starlette import status

from pecha_api.db.database import SessionLocal
from pecha_api.group_posts.notification_repository import get_group_notification_title
from pecha_api.notification.notification_preference_enums import (
    GROUP_SCOPED_TYPES,
    NON_TOGGLEABLE_TYPES,
    NotificationChannel,
    NotificationType,
    PreferenceSource,
    V1_GROUP_TOGGLEABLE_TYPES,
    V1_TOGGLEABLE_TYPES,
)
from pecha_api.notification.notification_preference_models import (
    UserNotificationPreference,
)
from pecha_api.notification.notification_preference_repository import (
    delete_group_preferences,
    index_by_key,
    list_preferences_for_user,
    upsert_preference,
)
from pecha_api.notification.notification_preference_response_models import (
    EffectivePreferenceDTO,
    GroupNotificationPreferencesResponse,
    GroupOverrideSummaryDTO,
    NotificationPreferenceUpdateDTO,
    NotificationPreferencesResponse,
    UpdateNotificationPreferencesRequest,
)
from pecha_api.plans.groups.groups_repository import is_user_joined_group
from pecha_api.users.users_service import validate_and_extract_user_details

NOT_A_MEMBER = "You are not a member of this group"


def _as_utc(value: Optional[datetime]) -> Optional[datetime]:
    if value is None:
        return None
    return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)


def _reject(detail: str) -> None:
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=detail,
    )


def _validate_type(notification_type: NotificationType, *, group_scoped: bool) -> None:
    if notification_type in NON_TOGGLEABLE_TYPES:
        _reject(
            f"{notification_type.value} is transactional and cannot be toggled"
        )
    if group_scoped and notification_type not in GROUP_SCOPED_TYPES:
        _reject(
            f"{notification_type.value} has no per-group setting; "
            f"set it globally instead"
        )


def _expand(
    entry: NotificationPreferenceUpdateDTO,
    *,
    group_scoped: bool,
) -> Sequence[NotificationType]:
    """Resolve one PATCH entry to the types it writes.

    `ALL` is sugar so a "Mute this group" button need not enumerate types; it
    never reaches the database.
    """
    if entry.is_all_types:
        return V1_GROUP_TOGGLEABLE_TYPES if group_scoped else V1_TOGGLEABLE_TYPES

    notification_type = NotificationType[entry.notification_type]
    _validate_type(notification_type, group_scoped=group_scoped)
    return (notification_type,)


def _resolve(
    notification_type: NotificationType,
    *,
    group_row: Optional[UserNotificationPreference],
    global_row: Optional[UserNotificationPreference],
    now: datetime,
) -> EffectivePreferenceDTO:
    """RFC §5: `enabled` is most-specific-wins, `muted_until` is any-row-suppresses."""
    if group_row is not None:
        enabled = bool(group_row.enabled)
        source = PreferenceSource.GROUP
    elif global_row is not None:
        enabled = bool(global_row.enabled)
        source = PreferenceSource.GLOBAL
    else:
        enabled = True
        source = PreferenceSource.DEFAULT

    active_mutes = [
        muted_until
        for muted_until in (
            _as_utc(group_row.muted_until if group_row else None),
            _as_utc(global_row.muted_until if global_row else None),
        )
        if muted_until is not None and muted_until > now
    ]

    return EffectivePreferenceDTO(
        notification_type=notification_type,
        enabled=enabled,
        muted_until=max(active_mutes) if active_mutes else None,
        source=source,
    )


def _effective_preferences(
    types: Sequence[NotificationType],
    rows_by_key: Dict[Tuple[NotificationType, Optional[UUID]], UserNotificationPreference],
    *,
    group_id: Optional[UUID],
    now: datetime,
) -> List[EffectivePreferenceDTO]:
    return [
        _resolve(
            notification_type,
            group_row=(
                rows_by_key.get((notification_type, group_id))
                if group_id is not None
                else None
            ),
            global_row=rows_by_key.get((notification_type, None)),
            now=now,
        )
        for notification_type in types
    ]


def _group_override_summaries(
    db: Session,
    rows: List[UserNotificationPreference],
    *,
    now: datetime,
) -> List[GroupOverrideSummaryDTO]:
    """A flat index for a settings screen — not a resolution.

    Lets a client list "Groups with custom settings" without a request per
    group; the per-group GET gives the resolved detail.
    """
    by_group: Dict[UUID, List[UserNotificationPreference]] = {}
    for row in rows:
        by_group.setdefault(row.scope_id, []).append(row)

    summaries: List[GroupOverrideSummaryDTO] = []
    for group_id, group_rows in by_group.items():
        active_mutes = [
            muted_until
            for muted_until in (_as_utc(row.muted_until) for row in group_rows)
            if muted_until is not None and muted_until > now
        ]
        summaries.append(
            GroupOverrideSummaryDTO(
                group_id=group_id,
                group_title=get_group_notification_title(db, group_id),
                overridden_types=sorted(
                    {row.notification_type for row in group_rows},
                    key=lambda notification_type: notification_type.value,
                ),
                muted_until=max(active_mutes) if active_mutes else None,
            )
        )
    return sorted(summaries, key=lambda summary: summary.group_title)


def _assert_group_member(db: Session, *, group_id: UUID, user_id: UUID) -> None:
    if not is_user_joined_group(db=db, group_id=group_id, user_id=user_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=NOT_A_MEMBER,
        )


@dataclass
class _PendingChange:
    """The fields one PATCH body ends up writing for a single type."""

    enabled: Optional[bool] = None
    muted_until: Optional[datetime] = None
    set_enabled: bool = False
    set_muted_until: bool = False

    def merge(self, entry: NotificationPreferenceUpdateDTO) -> None:
        if entry.sets_enabled:
            self.enabled = entry.enabled
            self.set_enabled = True
        if entry.sets_muted_until:
            self.muted_until = entry.muted_until
            self.set_muted_until = True


def _collect_changes(
    request: UpdateNotificationPreferencesRequest,
    *,
    group_scoped: bool,
    now: datetime,
) -> Dict[NotificationType, _PendingChange]:
    """Fold the body into at most one write per type.

    One body can name the same type twice — `ALL` to mute a group, then an
    explicit type to keep one thing on — and two writes for one key would
    stage two inserts that collide on the unique index at commit. Folding
    first also gives the later entry the last word field by field, which is
    the same merge rule PATCH already applies across requests.
    """
    changes: Dict[NotificationType, _PendingChange] = {}

    for entry in request.preferences:
        if entry.sets_muted_until and entry.muted_until is not None:
            if _as_utc(entry.muted_until) <= now:
                _reject("muted_until must be in the future")

        if not entry.sets_enabled and not entry.sets_muted_until:
            _reject(
                f"{entry.notification_type} names no change; "
                f"send enabled, muted_until, or both"
            )

        for notification_type in _expand(entry, group_scoped=group_scoped):
            changes.setdefault(notification_type, _PendingChange()).merge(entry)

    return changes


def _apply_updates(
    db: Session,
    *,
    user_id: UUID,
    channel: NotificationChannel,
    scope_id: Optional[UUID],
    request: UpdateNotificationPreferencesRequest,
    now: datetime,
) -> None:
    changes = _collect_changes(
        request,
        group_scoped=scope_id is not None,
        now=now,
    )

    for notification_type, change in changes.items():
        upsert_preference(
            db=db,
            user_id=user_id,
            notification_type=notification_type,
            channel=channel,
            scope_id=scope_id,
            enabled=change.enabled,
            muted_until=change.muted_until,
            set_enabled=change.set_enabled,
            set_muted_until=change.set_muted_until,
        )

    db.commit()


def get_notification_preferences_service(
    token: str,
    channel: NotificationChannel = NotificationChannel.PUSH,
) -> NotificationPreferencesResponse:
    current_user = validate_and_extract_user_details(token=token)
    now = datetime.now(timezone.utc)

    with SessionLocal() as db:
        rows = list_preferences_for_user(db=db, user_id=current_user.id, channel=channel)
        global_rows = [row for row in rows if row.scope_id is None]
        group_rows = [row for row in rows if row.scope_id is not None]

        return NotificationPreferencesResponse(
            channel=channel,
            preferences=_effective_preferences(
                V1_TOGGLEABLE_TYPES,
                index_by_key(global_rows),
                group_id=None,
                now=now,
            ),
            group_overrides=_group_override_summaries(db, group_rows, now=now),
        )


def update_notification_preferences_service(
    token: str,
    request: UpdateNotificationPreferencesRequest,
    channel: NotificationChannel = NotificationChannel.PUSH,
) -> NotificationPreferencesResponse:
    current_user = validate_and_extract_user_details(token=token)
    now = datetime.now(timezone.utc)

    with SessionLocal() as db:
        _apply_updates(
            db=db,
            user_id=current_user.id,
            channel=channel,
            scope_id=None,
            request=request,
            now=now,
        )

        rows = list_preferences_for_user(db=db, user_id=current_user.id, channel=channel)
        global_rows = [row for row in rows if row.scope_id is None]
        group_rows = [row for row in rows if row.scope_id is not None]

        return NotificationPreferencesResponse(
            channel=channel,
            preferences=_effective_preferences(
                V1_TOGGLEABLE_TYPES,
                index_by_key(global_rows),
                group_id=None,
                now=now,
            ),
            group_overrides=_group_override_summaries(db, group_rows, now=now),
        )


def get_group_notification_preferences_service(
    token: str,
    group_id: UUID,
    channel: NotificationChannel = NotificationChannel.PUSH,
) -> GroupNotificationPreferencesResponse:
    current_user = validate_and_extract_user_details(token=token)
    now = datetime.now(timezone.utc)

    with SessionLocal() as db:
        _assert_group_member(db, group_id=group_id, user_id=current_user.id)

        rows = list_preferences_for_user(
            db=db,
            user_id=current_user.id,
            channel=channel,
            scope_id=group_id,
        )

        return GroupNotificationPreferencesResponse(
            group_id=group_id,
            channel=channel,
            preferences=_effective_preferences(
                V1_GROUP_TOGGLEABLE_TYPES,
                index_by_key(rows),
                group_id=group_id,
                now=now,
            ),
        )


def update_group_notification_preferences_service(
    token: str,
    group_id: UUID,
    request: UpdateNotificationPreferencesRequest,
    channel: NotificationChannel = NotificationChannel.PUSH,
) -> GroupNotificationPreferencesResponse:
    current_user = validate_and_extract_user_details(token=token)
    now = datetime.now(timezone.utc)

    with SessionLocal() as db:
        _assert_group_member(db, group_id=group_id, user_id=current_user.id)

        _apply_updates(
            db=db,
            user_id=current_user.id,
            channel=channel,
            scope_id=group_id,
            request=request,
            now=now,
        )

        rows = list_preferences_for_user(
            db=db,
            user_id=current_user.id,
            channel=channel,
            scope_id=group_id,
        )

        return GroupNotificationPreferencesResponse(
            group_id=group_id,
            channel=channel,
            preferences=_effective_preferences(
                V1_GROUP_TOGGLEABLE_TYPES,
                index_by_key(rows),
                group_id=group_id,
                now=now,
            ),
        )


def delete_group_notification_preferences_service(
    token: str,
    group_id: UUID,
    notification_type: Optional[NotificationType] = None,
    channel: NotificationChannel = NotificationChannel.PUSH,
) -> None:
    current_user = validate_and_extract_user_details(token=token)

    with SessionLocal() as db:
        _assert_group_member(db, group_id=group_id, user_id=current_user.id)

        if notification_type is not None:
            _validate_type(notification_type, group_scoped=True)

        # Deleting rows that do not exist is not an error: the caller's intent
        # is "fall back to global", which is already true.
        delete_group_preferences(
            db=db,
            user_id=current_user.id,
            group_id=group_id,
            channel=channel,
            notification_type=notification_type,
        )
