from datetime import datetime, timezone
from typing import Dict, List, Optional, Sequence, Tuple
from uuid import UUID

from sqlalchemy import func, or_
from sqlalchemy.orm import Session, selectinload

from pecha_api.chat.enums import ChatMessageReportSource, ChatRoomMemberRole
from pecha_api.chat.models import (
    ChatMessage,
    ChatMessageReaction,
    ChatMessageReport,
    ChatRoom,
    ChatRoomMember,
)


def get_room_by_id(db: Session, room_id: UUID) -> Optional[ChatRoom]:
    return (
        db.query(ChatRoom)
        .filter(ChatRoom.id == room_id, ChatRoom.deleted_at.is_(None))
        .first()
    )


def get_room_by_group_id(db: Session, group_id: UUID) -> Optional[ChatRoom]:
    return (
        db.query(ChatRoom)
        .filter(ChatRoom.group_id == group_id, ChatRoom.deleted_at.is_(None))
        .first()
    )


def get_room_by_pair(db: Session, low_id: UUID, high_id: UUID) -> Optional[ChatRoom]:
    return (
        db.query(ChatRoom)
        .filter(
            ChatRoom.sender_id == low_id,
            ChatRoom.receiver_id == high_id,
            ChatRoom.deleted_at.is_(None),
        )
        .first()
    )


def create_room(db: Session, room: ChatRoom) -> ChatRoom:
    db.add(room)
    db.commit()
    db.refresh(room)
    return room


def update_room(db: Session, room: ChatRoom) -> ChatRoom:
    room.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(room)
    return room


def touch_room(db: Session, room: ChatRoom) -> None:
    room.updated_at = datetime.now(timezone.utc)
    db.commit()


def add_member(db: Session, member: ChatRoomMember) -> ChatRoomMember:
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


def get_member(db: Session, room_id: UUID, user_id: UUID) -> Optional[ChatRoomMember]:
    return (
        db.query(ChatRoomMember)
        .filter(ChatRoomMember.room_id == room_id, ChatRoomMember.user_id == user_id)
        .first()
    )


def get_active_member(db: Session, room_id: UUID, user_id: UUID) -> Optional[ChatRoomMember]:
    return (
        db.query(ChatRoomMember)
        .filter(
            ChatRoomMember.room_id == room_id,
            ChatRoomMember.user_id == user_id,
            ChatRoomMember.left_at.is_(None),
        )
        .first()
    )


def get_creator(db: Session, room_id: UUID) -> Optional[ChatRoomMember]:
    return (
        db.query(ChatRoomMember)
        .filter(
            ChatRoomMember.room_id == room_id,
            ChatRoomMember.role == ChatRoomMemberRole.CREATOR.value,
            ChatRoomMember.left_at.is_(None),
        )
        .first()
    )


def list_active_members(
    db: Session,
    room_id: UUID,
    skip: int = 0,
    limit: int = 20,
) -> Tuple[List[ChatRoomMember], int]:
    query = (
        db.query(ChatRoomMember)
        .options(selectinload(ChatRoomMember.user))
        .filter(ChatRoomMember.room_id == room_id, ChatRoomMember.left_at.is_(None))
    )
    total = query.count()
    members = query.order_by(ChatRoomMember.joined_at.asc()).offset(skip).limit(limit).all()
    return members, total


def count_active_members(db: Session, room_id: UUID) -> int:
    return (
        db.query(func.count(ChatRoomMember.id))
        .filter(ChatRoomMember.room_id == room_id, ChatRoomMember.left_at.is_(None))
        .scalar()
        or 0
    )


def leave_member(db: Session, member: ChatRoomMember) -> None:
    member.left_at = datetime.now(timezone.utc)
    db.commit()


def mark_read(db: Session, member: ChatRoomMember) -> None:
    member.last_read_at = datetime.now(timezone.utc)
    db.commit()


def list_my_active_rooms(
    db: Session,
    user_id: UUID,
    skip: int = 0,
    limit: int = 20,
) -> Tuple[List[ChatRoom], int]:
    query = (
        db.query(ChatRoom)
        .join(ChatRoomMember, ChatRoomMember.room_id == ChatRoom.id)
        .filter(
            ChatRoomMember.user_id == user_id,
            ChatRoomMember.left_at.is_(None),
            ChatRoom.deleted_at.is_(None),
        )
    )
    total = query.count()
    rooms = (
        query.order_by(ChatRoom.updated_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return rooms, total


def create_message(db: Session, message: ChatMessage) -> ChatMessage:
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def get_room_messages(
    db: Session,
    room_id: UUID,
    skip: int = 0,
    limit: int = 20,
) -> Tuple[List[ChatMessage], int]:
    query = (
        db.query(ChatMessage)
        .filter(ChatMessage.room_id == room_id, ChatMessage.deleted_at.is_(None))
        .order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc())
    )
    total = query.count()
    messages = (
        query.options(
            selectinload(ChatMessage.sender),
            selectinload(ChatMessage.parent).selectinload(ChatMessage.sender),
        )
        .offset(skip)
        .limit(limit)
        .all()
    )
    return messages, total


def get_message_by_id(db: Session, message_id: UUID, room_id: UUID) -> Optional[ChatMessage]:
    return (
        db.query(ChatMessage)
        .filter(
            ChatMessage.id == message_id,
            ChatMessage.room_id == room_id,
            ChatMessage.deleted_at.is_(None),
        )
        .first()
    )


def soft_delete_message(db: Session, message: ChatMessage) -> None:
    message.deleted_at = datetime.now(timezone.utc)
    db.commit()


def mark_message_notification_dispatched(
    db: Session,
    message_id: UUID,
    sqs_message_id: str,
) -> Optional[ChatMessage]:
    message = (
        db.query(ChatMessage)
        .filter(
            ChatMessage.id == message_id,
            ChatMessage.deleted_at.is_(None),
        )
        .first()
    )
    if not message:
        return None
    message.notification_sqs_message_id = sqs_message_id
    message.notification_dispatched_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(message)
    return message


def list_undispatched_chat_notification_messages(
    db: Session,
    *,
    older_than: datetime,
    limit: int,
) -> List[ChatMessage]:
    return (
        db.query(ChatMessage)
        .filter(
            ChatMessage.deleted_at.is_(None),
            ChatMessage.notification_sqs_message_id.is_(None),
            ChatMessage.created_at <= older_than,
        )
        .order_by(ChatMessage.created_at.asc())
        .limit(limit)
        .all()
    )


def get_message_by_id_any_room(db: Session, message_id: UUID) -> Optional[ChatMessage]:
    return (
        db.query(ChatMessage)
        .options(
            selectinload(ChatMessage.sender),
            selectinload(ChatMessage.room),
        )
        .filter(
            ChatMessage.id == message_id,
            ChatMessage.deleted_at.is_(None),
        )
        .first()
    )


def get_last_message(db: Session, room_id: UUID) -> Optional[ChatMessage]:
    return (
        db.query(ChatMessage)
        .options(selectinload(ChatMessage.sender))
        .filter(ChatMessage.room_id == room_id, ChatMessage.deleted_at.is_(None))
        .order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc())
        .first()
    )


def get_last_messages_map(db: Session, room_ids: Sequence[UUID]) -> Dict[UUID, ChatMessage]:
    if not room_ids:
        return {}
    messages = (
        db.query(ChatMessage)
        .options(selectinload(ChatMessage.sender))
        .filter(ChatMessage.room_id.in_(room_ids), ChatMessage.deleted_at.is_(None))
        .order_by(ChatMessage.room_id, ChatMessage.created_at.desc(), ChatMessage.id.desc())
        .all()
    )
    result: Dict[UUID, ChatMessage] = {}
    for message in messages:
        if message.room_id not in result:
            result[message.room_id] = message
    return result


def get_reaction(
    db: Session,
    message_id: UUID,
    user_id: UUID,
    emoji: str,
) -> Optional[ChatMessageReaction]:
    return (
        db.query(ChatMessageReaction)
        .filter(
            ChatMessageReaction.message_id == message_id,
            ChatMessageReaction.user_id == user_id,
            ChatMessageReaction.emoji == emoji,
        )
        .first()
    )


def add_reaction(db: Session, reaction: ChatMessageReaction) -> ChatMessageReaction:
    db.add(reaction)
    db.commit()
    db.refresh(reaction)
    return reaction


def remove_reaction(db: Session, reaction: ChatMessageReaction) -> None:
    db.delete(reaction)
    db.commit()


def list_message_reactions(db: Session, message_id: UUID) -> List[ChatMessageReaction]:
    return (
        db.query(ChatMessageReaction)
        .filter(ChatMessageReaction.message_id == message_id)
        .order_by(ChatMessageReaction.created_at.asc())
        .all()
    )


def get_reactions_map(
    db: Session,
    message_ids: Sequence[UUID],
) -> Dict[UUID, List[ChatMessageReaction]]:
    """Reactions for many messages at once, keyed by message_id."""
    if not message_ids:
        return {}
    reactions = (
        db.query(ChatMessageReaction)
        .filter(ChatMessageReaction.message_id.in_(message_ids))
        .order_by(ChatMessageReaction.created_at.asc())
        .all()
    )
    result: Dict[UUID, List[ChatMessageReaction]] = {}
    for reaction in reactions:
        result.setdefault(reaction.message_id, []).append(reaction)
    return result


def get_report_by_message_and_reporter(
    db: Session,
    message_id: UUID,
    reporter_id: UUID,
) -> Optional[ChatMessageReport]:
    return (
        db.query(ChatMessageReport)
        .filter(
            ChatMessageReport.message_id == message_id,
            ChatMessageReport.reporter_id == reporter_id,
        )
        .first()
    )


def list_reports(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    source: Optional[str] = None,
    reason: Optional[str] = None,
    resolved: Optional[bool] = None,
) -> Tuple[List[ChatMessageReport], int]:
    """Paginated moderation reports, newest first, with the people and
    message context eagerly loaded for display."""
    query = db.query(ChatMessageReport)
    if source:
        query = query.filter(ChatMessageReport.source == source)
    if reason:
        query = query.filter(ChatMessageReport.reason == reason)
    if resolved is True:
        query = query.filter(ChatMessageReport.resolved_at.isnot(None))
    elif resolved is False:
        query = query.filter(ChatMessageReport.resolved_at.is_(None))
    total = query.with_entities(func.count(ChatMessageReport.id)).scalar() or 0
    reports = (
        query.options(
            selectinload(ChatMessageReport.reporter),
            selectinload(ChatMessageReport.reported_user),
            selectinload(ChatMessageReport.room),
            selectinload(ChatMessageReport.message).selectinload(ChatMessage.sender),
            selectinload(ChatMessageReport.message).selectinload(ChatMessage.room),
        )
        .order_by(ChatMessageReport.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return reports, total


def get_unresolved_automatic_report(
    db: Session,
    room_id: UUID,
    reported_user_id: UUID,
    message_text: str,
) -> Optional[ChatMessageReport]:
    """An open system-generated report for the same rejected content, used to
    keep retried sends of the same message from piling up duplicate reports."""
    return (
        db.query(ChatMessageReport)
        .filter(
            ChatMessageReport.source == ChatMessageReportSource.AUTOMATIC.value,
            ChatMessageReport.room_id == room_id,
            ChatMessageReport.reported_user_id == reported_user_id,
            ChatMessageReport.message_text == message_text,
            ChatMessageReport.resolved_at.is_(None),
        )
        .first()
    )


def create_report(db: Session, report: ChatMessageReport) -> ChatMessageReport:
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def count_unread_messages(
    db: Session,
    room_id: UUID,
    last_read_at: Optional[datetime],
) -> int:
    query = db.query(func.count(ChatMessage.id)).filter(
        ChatMessage.room_id == room_id,
        ChatMessage.deleted_at.is_(None),
    )
    if last_read_at is not None:
        query = query.filter(ChatMessage.created_at > last_read_at)
    return query.scalar() or 0
