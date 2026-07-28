from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session
from starlette import status

from pecha_api.chat.models import ChatMessage, ChatRoom
from pecha_api.chat.repository import (
    create_message,
    get_message_by_id,
    get_room_messages,
    soft_delete_message,
    touch_room,
)
from pecha_api.chat.response_models import ChatMessageDTO, ChatMessagesResponse
from pecha_api.chat.service import (
    _get_room_or_404,
    _require_active_member,
    build_message_dto,
    resolve_or_create_group_room,
    resolve_or_create_private_room,
)
from pecha_api.db.database import SessionLocal
from pecha_api.plans.response_message import NOT_FOUND
from pecha_api.users.users_models import Users


def send_group_message_service(group_id: UUID, user: Users, body: str) -> ChatMessageDTO:
    with SessionLocal() as db:
        room = resolve_or_create_group_room(db=db, group_id=group_id, user=user)
        _require_active_member(db=db, room_id=room.id, user_id=user.id)
        return _persist_message(db=db, room=room, user=user, body=body)


def send_direct_message_service(receiver_id: UUID, user: Users, body: str) -> ChatMessageDTO:
    with SessionLocal() as db:
        room = resolve_or_create_private_room(db=db, user=user, receiver_id=receiver_id)
        return _persist_message(db=db, room=room, user=user, body=body)


def _persist_message(db: Session, room: ChatRoom, user: Users, body: str) -> ChatMessageDTO:
    message = ChatMessage(room_id=room.id, sender_id=user.id, body=body)
    message = create_message(db=db, message=message)
    message.sender = user
    touch_room(db=db, room=room)
    return build_message_dto(message)


def list_room_messages_service(
    room_id: UUID,
    user: Users,
    skip: int = 0,
    limit: int = 20,
) -> ChatMessagesResponse:
    with SessionLocal() as db:
        _get_room_or_404(db=db, room_id=room_id)
        _require_active_member(db=db, room_id=room_id, user_id=user.id)

        messages, total = get_room_messages(db=db, room_id=room_id, skip=skip, limit=limit)
        return ChatMessagesResponse(
            messages=[build_message_dto(message) for message in messages],
            skip=skip,
            limit=limit,
            total=total,
        )


def delete_message_service(room_id: UUID, message_id: UUID, user: Users) -> None:
    with SessionLocal() as db:
        _get_room_or_404(db=db, room_id=room_id)
        _require_active_member(db=db, room_id=room_id, user_id=user.id)

        message = get_message_by_id(db=db, message_id=message_id, room_id=room_id)
        if not message:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NOT_FOUND)

        if message.sender_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own messages",
            )

        soft_delete_message(db=db, message=message)
