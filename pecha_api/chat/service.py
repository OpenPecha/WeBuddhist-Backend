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
from pecha_api.chat.response_models import (
    ChatMessageDTO,
    ChatMessageParentDTO,
    ChatMessageReactionDTO,
    ChatMessageReactionUserDTO,
    ChatPeopleResponse,
    ChatPersonDTO,
    ChatRoomDTO,
    ChatRoomsResponse,
)
from pecha_api.config import get
from pecha_api.db.database import SessionLocal
from pecha_api.plans.groups.groups_models import AuthorGroup
from pecha_api.plans.groups.groups_repository import (
    get_group_by_id,
    is_group_id_published,
    is_group_published,
    is_user_following_group,
    is_user_joined_group,
    list_group_joiners_paginated,
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


def _build_reaction_dtos(reactions, viewer_id: Optional[UUID]) -> list:
    """Aggregate reaction rows into per-emoji summaries (first-seen order)."""
    if not reactions:
        return []
    summaries: dict = {}
    for reaction in reactions:
        summary = summaries.setdefault(
            reaction.emoji,
            ChatMessageReactionDTO(emoji=reaction.emoji, count=0, reacted_by_me=False),
        )
        summary.count += 1
        summary.user_ids.append(reaction.user_id)
        user = getattr(reaction, "user", None)
        summary.users.append(
            ChatMessageReactionUserDTO(
                user_id=reaction.user_id,
                email=user.email if user else None,
                name=(
                    f"{user.firstname} {user.lastname or ''}".strip() or user.email
                )
                if user
                else None,
            )
        )
        if viewer_id is not None and reaction.user_id == viewer_id:
            summary.reacted_by_me = True
    return list(summaries.values())


def _build_parent_dto(message: ChatMessage) -> Optional[ChatMessageParentDTO]:
    has_parent = getattr(message, "parent_message_id", None) is not None
    parent = getattr(message, "parent", None) if has_parent else None
    if parent is None or parent.deleted_at is not None:
        return None
    return ChatMessageParentDTO(
        id=parent.id,
        sender_id=parent.sender_id,
        sender_email=parent.sender.email if parent.sender else "unknown@example.com",
        body=parent.body,
        created_at=_isoformat(parent.created_at),
    )


def build_message_dto(
    message: ChatMessage,
    reactions=None,
    viewer_id: Optional[UUID] = None,
) -> ChatMessageDTO:
    sender_email = message.sender.email if message.sender else "unknown@example.com"
    return ChatMessageDTO(
        id=message.id,
        room_id=message.room_id,
        sender_id=message.sender_id,
        sender_email=sender_email,
        body=message.body,
        created_at=_isoformat(message.created_at),
        parent=_build_parent_dto(message),
        reactions=_build_reaction_dtos(reactions, viewer_id),
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

    other_user_id = other_user_email = other_user_name = None
    if room.group_id is None:
        other_id = room.receiver_id if room.sender_id == viewer_id else room.sender_id
        other_user = db.query(Users).filter(Users.id == other_id).first()
        if other_user:
            other_user_id = other_user.id
            other_user_email = other_user.email
            other_user_name = f"{other_user.firstname} {other_user.lastname or ''}".strip()

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
        other_user_id=other_user_id,
        other_user_email=other_user_email,
        other_user_name=other_user_name,
    )


def _default_group_room_name(group: AuthorGroup) -> str:
    if group.metadata_entries:
        return group.metadata_entries[0].title
    return group.slug


def _is_eligible_for_group_chat(db: Session, group_id: UUID, user_id: UUID) -> bool:
    return is_user_joined_group(
        db=db, group_id=group_id, user_id=user_id
    ) or is_user_following_group(db=db, group_id=group_id, user_id=user_id)


def _require_group_chat_eligibility(db: Session, group_id: UUID, user_id: UUID) -> None:
    if not _is_eligible_for_group_chat(db=db, group_id=group_id, user_id=user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only joined or following members of this group can send messages in its chat",
        )


def resolve_or_create_group_room(
    db: Session,
    group_id: UUID,
    user: Users,
    lock_group: bool = False,
) -> ChatRoom:
    """Get the group's chat room, auto-creating it (with the caller as CREATOR)
    on the first message if the caller is a joiner/follower of the group. Any
    other joiner/follower is auto-added (or re-activated) as a MEMBER the
    first time they reach an already-existing room."""
    # Checked before the existing-room shortcut: a room created while the group
    # was live must stop serving once the group is hidden. Status-only lookup,
    # since this runs on every message send. Callers that go on to write (i.e.
    # sending a message) pass lock_group=True so a concurrent hide cannot land
    # between this check and the commit.
    if not is_group_id_published(db=db, group_id=group_id, for_update=lock_group):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NOT_FOUND)

    room = get_room_by_group_id(db=db, group_id=group_id)
    if room is not None:
        member = get_member(db=db, room_id=room.id, user_id=user.id)
        if member is None or member.left_at is not None:
            _require_group_chat_eligibility(db=db, group_id=group_id, user_id=user.id)
            if member is None:
                add_member(
                    db=db,
                    member=ChatRoomMember(
                        room_id=room.id,
                        user_id=user.id,
                        role=ChatRoomMemberRole.MEMBER.value,
                    ),
                )
            else:
                member.left_at = None
                db.commit()
        return room

    _require_group_chat_eligibility(db=db, group_id=group_id, user_id=user.id)

    # Full object needed here for the room's name and avatar.
    group = get_group_by_id(db=db, group_id=group_id)
    if group is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NOT_FOUND)

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
    # Every room-id route resolves through here, so gating the group's
    # publication status once closes detail, history, reactions, reports and
    # member operations together. DM rooms have no group_id and are unaffected.
    if room.group_id is not None and not is_group_id_published(
        db=db, group_id=room.group_id
    ):
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


def list_group_people_service(
    group_id: UUID,
    user: Users,
    skip: int = 0,
    limit: int = 50,
) -> ChatPeopleResponse:
    """List a group's joiners as DM candidates (excluding the caller), so a
    client can start a direct chat without already knowing a user_id."""
    with SessionLocal() as db:
        group = get_group_by_id(db=db, group_id=group_id)
        if not group or not is_group_published(group):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NOT_FOUND)

        users, total = list_group_joiners_paginated(db=db, group_id=group_id, skip=skip, limit=limit)
        return ChatPeopleResponse(
            people=[
                ChatPersonDTO(
                    user_id=joiner.id,
                    email=joiner.email,
                    firstname=joiner.firstname,
                    lastname=joiner.lastname,
                    avatar_url=joiner.avatar_url,
                )
                for joiner in users
                if joiner.id != user.id
            ],
            skip=skip,
            limit=limit,
            total=total,
        )
