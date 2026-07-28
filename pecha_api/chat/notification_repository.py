from collections import defaultdict
from typing import Dict, List, Optional, Sequence, Tuple
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from pecha_api.chat.models import ChatRoom
from pecha_api.plans.groups.groups_models import author_group_joins
from pecha_api.push_devices.push_device_models import PushDeviceToken
from pecha_api.users.users_models import Users


def _normalize_platform(value) -> str:
    raw = value.value if hasattr(value, "value") else str(value)
    if "." in raw:
        raw = raw.rsplit(".", 1)[-1]
    return raw.lower()


def list_private_chat_recipient_user_ids(
    *,
    room: ChatRoom,
    sender_id: UUID,
) -> List[UUID]:
    if room.sender_id == sender_id:
        return [room.receiver_id] if room.receiver_id else []
    if room.receiver_id == sender_id:
        return [room.sender_id] if room.sender_id else []
    return []


def list_group_chat_recipient_user_ids(
    db: Session,
    *,
    group_id: UUID,
    sender_id: UUID,
    skip: int,
    limit: int,
) -> Tuple[List[UUID], int]:
    base = (
        select(author_group_joins.c.user_id)
        .where(
            author_group_joins.c.group_id == group_id,
            author_group_joins.c.user_id != sender_id,
        )
        .order_by(author_group_joins.c.created_at.asc(), author_group_joins.c.user_id.asc())
    )
    total = (
        db.execute(
            select(func.count())
            .select_from(author_group_joins)
            .where(
                author_group_joins.c.group_id == group_id,
                author_group_joins.c.user_id != sender_id,
            )
        ).scalar()
        or 0
    )
    rows = db.execute(base.offset(skip).limit(limit)).all()
    return [row[0] for row in rows], int(total)


def get_active_push_devices_by_user_ids(
    db: Session,
    user_ids: Sequence[UUID],
) -> Dict[UUID, List[PushDeviceToken]]:
    if not user_ids:
        return {}
    rows = (
        db.query(PushDeviceToken)
        .filter(
            PushDeviceToken.user_id.in_(list(user_ids)),
            PushDeviceToken.is_active.is_(True),
        )
        .order_by(PushDeviceToken.updated_at.desc())
        .all()
    )
    result: Dict[UUID, List[PushDeviceToken]] = defaultdict(list)
    for device in rows:
        result[device.user_id].append(device)
    return dict(result)


def deactivate_push_device_token_by_id(
    db: Session,
    push_device_id: UUID,
) -> Optional[PushDeviceToken]:
    device = (
        db.query(PushDeviceToken)
        .filter(PushDeviceToken.id == push_device_id)
        .first()
    )
    if not device:
        return None
    if not device.is_active:
        return device
    device.is_active = False
    db.commit()
    db.refresh(device)
    return device


def get_sender_display_name(db: Session, sender_id: UUID) -> str:
    user = db.query(Users).filter(Users.id == sender_id).first()
    if not user:
        return "Someone"
    return f"{user.firstname} {user.lastname or ''}".strip() or user.email


def normalize_platform(value) -> str:
    return _normalize_platform(value)
