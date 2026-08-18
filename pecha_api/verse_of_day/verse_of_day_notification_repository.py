from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from pecha_api.push_devices.push_device_models import PushDeviceToken
from pecha_api.users.user_metadata_model import UserMetadata
from pecha_api.users.users_models import Users


def _enum_value(value) -> Optional[str]:
    if value is None:
        return None
    if hasattr(value, "value"):
        return str(value.value)
    raw = str(value)
    if "." in raw:
        return raw.rsplit(".", 1)[-1]
    return raw


def _normalize_platform(value) -> str:
    return (_enum_value(value) or "").lower()


@dataclass(frozen=True)
class VerseOfDayDeviceTargetRow:
    user_id: UUID
    device_token: str
    platform: str
    timezone: Optional[str]
    language: Optional[str]


def get_active_device_targets(db: Session) -> list[VerseOfDayDeviceTargetRow]:
    """All active push devices for active users, LEFT JOINed to their optional UserMetadata."""
    stmt = (
        select(
            PushDeviceToken.user_id,
            PushDeviceToken.token,
            PushDeviceToken.platform,
            UserMetadata.timezone,
            UserMetadata.language,
        )
        .select_from(PushDeviceToken)
        .join(Users, Users.id == PushDeviceToken.user_id)
        .outerjoin(UserMetadata, UserMetadata.user_id == PushDeviceToken.user_id)
        .where(
            PushDeviceToken.is_active.is_(True),
            Users.is_active.isnot(False),
        )
    )
    rows = db.execute(stmt).all()
    return [
        VerseOfDayDeviceTargetRow(
            user_id=row.user_id,
            device_token=row.token,
            platform=_normalize_platform(row.platform),
            timezone=row.timezone,
            language=_enum_value(row.language),
        )
        for row in rows
    ]
