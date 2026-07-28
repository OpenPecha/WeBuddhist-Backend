import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session
from starlette import status

from pecha_api.chat.enums import ChatRoomMemberRole
from pecha_api.chat.models import ChatMessage, ChatRoom, ChatRoomMember
from pecha_api.chat.repository import (
    add_member,
    count_active_members,
    count_unread_messages,
    create_room,
    get_active_member,
    get_last_message,
    get_last_messages_map,
    get_member,
    get_room_by_group_id,
    get_room_by_id,
    get_room_by_pair,
    list_active_members,
    list_my_active_rooms,
    mark_read,
    update_room,
)
from pecha_api.chat.response_models import ChatMessageDTO, ChatRoomDTO, ChatRoomsResponse
from pecha_api.config import get
from pecha_api.db.database import SessionLocal
from pecha_api.plans.groups.groups_models import AuthorGroup
from pecha_api.plans.groups.groups_repository import (
    get_group_by_id,
    is_user_following_group,
    is_user_joined_group,
)
from pecha_api.plans.response_message import FORBIDDEN, NOT_FOUND
from pecha_api.uploads.S3_utils import generate_presigned_access_url
from pecha_api.users.users_models import Users

logger = logging.getLogger(__name__)


def _isoformat(value) -> Optional[str]:
    if value is None:
        return None
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def _generate_presigned_url(s3_key: Optional[str]) -> Optional[str]:
    if not s3_key:
        return None
    try:
        return generate_presigned_access_url(
            bucket_name=get("AWS_BUCKET_NAME"),
            s3_key=s3_key,
        )
    except Exception:
        logger.exception(f"Failed to generate presigned URL for {s3_key}")
        return None


def build_message_dto(message: ChatMessage) -> ChatMessageDTO:
    sender_email = message.sender.email if message.sender else "unknown@example.com"
    return ChatMessageDTO(
        id=message.id,
        room_id=message.room_id,
        sender_id=message.sender_id,
        sender_email=sender_email,
        body=message.body,
        created_at=_isoformat(message.created_at),
    )


def build_room_dto(
    db: Session,
    room: ChatRoom,
    viewer_id: UUID,
    last_message: Optional[ChatMessage] = None,
) -> ChatRoomDTO:
    if last_message is None:
        last_message = get_last_message(db=db, room_id=room.id)

    viewer_member = get_active_member(db=db, room_id=room.id, user_id=viewer_id)
    last_read_at = viewer_member.last_read_at if viewer_member else None
    unread_count = count_unread_messages(db=db, room_id=room.id, last_read_at=last_read_at)

    return ChatRoomDTO(
        id=room.id,
        group_id=room.group_id,
        sender_id=room.sender_id,
        receiver_id=room.receiver_id,
        kind="GROUP" if room.group_id is not None else "PRIVATE",
        name=room.name,
        img_url=_generate_presigned_url(room.img_url),
        created_by=room.created_by,
        member_count=count_active_members(db=db, room_id=room.id),
        updated_at=_isoformat(room.updated_at),
        last_message=build_message_dto(last_message) if last_message else None,
        unread_count=unread_count,
    )


def _default_group_room_name(group: AuthorGroup) -> str:
    if group.metadata_entries:
        return group.metadata_entries[0].title
    return group.slug


def resolve_or_create_group_room(db: Session, group_id: UUID, user: Users) -> ChatRoom:
    """Get the group's chat room, auto-creating it (with the caller as CREATOR)
    on the first message if the caller is a joiner/follower of the group."""
    room = get_room_by_group_id(db=db, group_id=group_id)
    if room is not None:
        return room

    group = get_group_by_id(db=db, group_id=group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NOT_FOUND)

    is_eligible = is_user_joined_group(
        db=db, group_id=group_id, user_id=user.id
    ) or is_user_following_group(db=db, group_id=group_id, user_id=user.id)
    if not is_eligible:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=FORBIDDEN)

    room = ChatRoom(
        group_id=group_id,
        name=_default_group_room_name(group),
        img_url=group.avatar_key,
        created_by=user.id,
    )
    room = create_room(db=db, room=room)
    add_member(
        db=db,
        member=ChatRoomMember(
            room_id=room.id,
            user_id=user.id,
            role=ChatRoomMemberRole.CREATOR.value,
        ),
    )
    return room


def resolve_or_create_private_room(db: Session, user: Users, receiver_id: UUID) -> ChatRoom:
    """Get the DM room between user and receiver_id, auto-creating it (with
    both as MEMBER) on the first message. Normalizes the pair so either
    direction resolves to the same room."""
    if receiver_id == user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot start a chat with yourself",
        )

    other = db.query(Users).filter(Users.id == receiver_id).first()
    if not other:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NOT_FOUND)

    low_id, high_id = sorted([user.id, receiver_id])
    room = get_room_by_pair(db=db, low_id=low_id, high_id=high_id)
    if room is not None:
        return room

    room = ChatRoom(
        sender_id=low_id,
        receiver_id=high_id,
        name=f"{user.firstname} & {other.firstname}",
        created_by=user.id,
    )
    room = create_room(db=db, room=room)
    for member_user_id in (low_id, high_id):
        add_member(
            db=db,
            member=ChatRoomMember(
                room_id=room.id,
                user_id=member_user_id,
                role=ChatRoomMemberRole.MEMBER.value,
            ),
        )
    return room


def _get_room_or_404(db: Session, room_id: UUID) -> ChatRoom:
    room = get_room_by_id(db=db, room_id=room_id)
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NOT_FOUND)
    return room


def _require_active_member(db: Session, room_id: UUID, user_id: UUID) -> ChatRoomMember:
    member = get_active_member(db=db, room_id=room_id, user_id=user_id)
    if not member:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=FORBIDDEN)
    return member


def get_room_detail_service(room_id: UUID, user: Users) -> ChatRoomDTO:
    with SessionLocal() as db:
        room = _get_room_or_404(db=db, room_id=room_id)
        _require_active_member(db=db, room_id=room_id, user_id=user.id)
        return build_room_dto(db=db, room=room, viewer_id=user.id)


def list_my_rooms_service(user: Users, skip: int = 0, limit: int = 20) -> ChatRoomsResponse:
    with SessionLocal() as db:
        rooms, total = list_my_active_rooms(db=db, user_id=user.id, skip=skip, limit=limit)
        last_messages = get_last_messages_map(db=db, room_ids=[room.id for room in rooms])
        return ChatRoomsResponse(
            rooms=[
                build_room_dto(
                    db=db,
                    room=room,
                    viewer_id=user.id,
                    last_message=last_messages.get(room.id),
                )
                for room in rooms
            ],
            skip=skip,
            limit=limit,
            total=total,
        )


def update_room_profile_service(
    room_id: UUID,
    user: Users,
    name: Optional[str],
    img_url: Optional[str],
) -> ChatRoomDTO:
    with SessionLocal() as db:
        room = _get_room_or_404(db=db, room_id=room_id)
        member = _require_active_member(db=db, room_id=room_id, user_id=user.id)

        if room.group_id is not None and member.role != ChatRoomMemberRole.CREATOR.value:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=FORBIDDEN)

        if name is not None:
            room.name = name
        if img_url is not None:
            room.img_url = img_url

        room = update_room(db=db, room=room)
        return build_room_dto(db=db, room=room, viewer_id=user.id)


def mark_room_read_service(room_id: UUID, user: Users) -> None:
    with SessionLocal() as db:
        _get_room_or_404(db=db, room_id=room_id)
        member = _require_active_member(db=db, room_id=room_id, user_id=user.id)
        mark_read(db=db, member=member)
