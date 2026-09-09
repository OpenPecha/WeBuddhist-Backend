from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from pecha_api.notification.notification_preference_enums import (
    NotificationChannel,
    NotificationScope,
    NotificationType,
)
from pecha_api.notification.notification_preference_models import (
    UserNotificationPreference,
)

PreferenceKey = Tuple[NotificationType, Optional[UUID]]


def list_preferences_for_user(
    db: Session,
    *,
    user_id: UUID,
    channel: NotificationChannel,
    scope_id: Optional[UUID] = None,
) -> List[UserNotificationPreference]:
    """Rows for one user on one channel.

    With `scope_id` set, narrows to that group's rows plus the global ones —
    exactly what resolving a single group needs. Without it, returns every row,
    which the global endpoint splits into globals and override summaries.
    """
    conditions = [
        UserNotificationPreference.user_id == user_id,
        UserNotificationPreference.channel == channel,
    ]
    if scope_id is not None:
        conditions.append(
            (UserNotificationPreference.scope_id == scope_id)
            | UserNotificationPreference.scope_id.is_(None)
        )

    return list(db.execute(select(UserNotificationPreference).where(*conditions)).scalars())


def index_by_key(
    rows: List[UserNotificationPreference],
) -> Dict[PreferenceKey, UserNotificationPreference]:
    return {(row.notification_type, row.scope_id): row for row in rows}


def get_preference(
    db: Session,
    *,
    user_id: UUID,
    notification_type: NotificationType,
    channel: NotificationChannel,
    scope_id: Optional[UUID],
) -> Optional[UserNotificationPreference]:
    scope_filter = (
        UserNotificationPreference.scope_id.is_(None)
        if scope_id is None
        else UserNotificationPreference.scope_id == scope_id
    )
    return db.execute(
        select(UserNotificationPreference).where(
            UserNotificationPreference.user_id == user_id,
            UserNotificationPreference.notification_type == notification_type,
            UserNotificationPreference.channel == channel,
            scope_filter,
        )
    ).scalar_one_or_none()


def upsert_preference(
    db: Session,
    *,
    user_id: UUID,
    notification_type: NotificationType,
    channel: NotificationChannel,
    scope_id: Optional[UUID],
    enabled: Optional[bool] = None,
    muted_until: Optional[datetime] = None,
    set_enabled: bool = False,
    set_muted_until: bool = False,
) -> UserNotificationPreference:
    """Merge one preference.

    `set_enabled` / `set_muted_until` say whether the client actually sent that
    field. A field that was not sent is left untouched on an existing row and
    falls back to its default on a new one.
    """
    existing = get_preference(
        db=db,
        user_id=user_id,
        notification_type=notification_type,
        channel=channel,
        scope_id=scope_id,
    )

    if existing is not None:
        if set_enabled:
            existing.enabled = bool(enabled)
        if set_muted_until:
            existing.muted_until = muted_until
        existing.updated_at = datetime.now(timezone.utc)
        db.add(existing)
        return existing

    preference = UserNotificationPreference(
        user_id=user_id,
        notification_type=notification_type,
        channel=channel,
        scope_type=(
            NotificationScope.GLOBAL if scope_id is None else NotificationScope.GROUP
        ),
        scope_id=scope_id,
        enabled=bool(enabled) if set_enabled else True,
        muted_until=muted_until if set_muted_until else None,
    )
    db.add(preference)
    return preference


def delete_group_preferences(
    db: Session,
    *,
    user_id: UUID,
    group_id: UUID,
    channel: NotificationChannel,
    notification_type: Optional[NotificationType] = None,
) -> int:
    conditions = [
        UserNotificationPreference.user_id == user_id,
        UserNotificationPreference.channel == channel,
        UserNotificationPreference.scope_id == group_id,
    ]
    if notification_type is not None:
        conditions.append(UserNotificationPreference.notification_type == notification_type)

    result = db.execute(delete(UserNotificationPreference).where(*conditions))
    db.commit()
    return int(result.rowcount or 0)
