from typing import List, Optional
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette import status

from pecha_api.chat.enums import ChatMessageReportReason, ChatMessageReportSource
from pecha_api.chat.models import (
    ChatMessage,
    ChatMessageReaction,
    ChatMessageReport,
    ChatRoom,
)
from pecha_api.chat.moderation_service import validate_message_content
from pecha_api.chat.notification_dispatch_service import enqueue_chat_message_notification
from pecha_api.chat.repository import (
    add_reaction,
    create_message,
    create_report,
    get_message_by_id,
    get_reaction,
    get_reactions_map,
    get_report_by_message_and_reporter,
    get_room_messages,
    list_message_reactions,
    remove_reaction,
    soft_delete_message,
    touch_room,
)
from pecha_api.chat.response_models import (
    ChatMessageDTO,
    ChatMessageReactionDTO,
    ChatMessagesResponse,
)
from pecha_api.chat.service import (
    _build_reaction_dtos,
    _get_room_or_404,
    _require_active_member,
    build_message_dto,
    resolve_or_create_group_room,
    resolve_or_create_private_room,
)
from pecha_api.db.database import SessionLocal
from pecha_api.plans.groups.groups_repository import is_group_id_published
from pecha_api.plans.response_message import NOT_FOUND
from pecha_api.users.users_models import Users

_PARENT_MESSAGE_NOT_FOUND = "PARENT_MESSAGE_NOT_FOUND"
_ALREADY_REPORTED = "ALREADY_REPORTED"
_CANNOT_REPORT_OWN_MESSAGE = "CANNOT_REPORT_OWN_MESSAGE"


def send_group_message_service(
    group_id: UUID,
    user: Users,
    body: str,
    parent_message_id: Optional[UUID] = None,
) -> ChatMessageDTO:
    with SessionLocal() as db:
        room = resolve_or_create_group_room(
            db=db, group_id=group_id, user=user, lock_group=True
        )
        _require_active_member(db=db, room_id=room.id, user_id=user.id)
        return _persist_message(
            db=db, room=room, user=user, body=body, parent_message_id=parent_message_id
        )


def send_direct_message_service(
    receiver_id: UUID,
    user: Users,
    body: str,
    parent_message_id: Optional[UUID] = None,
) -> ChatMessageDTO:
    with SessionLocal() as db:
        room = resolve_or_create_private_room(db=db, user=user, receiver_id=receiver_id)
        return _persist_message(
            db=db, room=room, user=user, body=body, parent_message_id=parent_message_id
        )


def _resolve_parent_message(
    db: Session, room: ChatRoom, parent_message_id: Optional[UUID]
) -> Optional[ChatMessage]:
    """A reply's parent must be an existing, non-deleted message in the same room."""
    if parent_message_id is None:
        return None
    parent = get_message_by_id(db=db, message_id=parent_message_id, room_id=room.id)
    if not parent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=_PARENT_MESSAGE_NOT_FOUND,
        )
    return parent


def _persist_message(
    db: Session,
    room: ChatRoom,
    user: Users,
    body: str,
    parent_message_id: Optional[UUID] = None,
) -> ChatMessageDTO:
    validate_message_content(db=db, room=room, user=user, body=body)
    parent = _resolve_parent_message(db=db, room=room, parent_message_id=parent_message_id)
    message = ChatMessage(
        room_id=room.id,
        sender_id=user.id,
        body=body,
        parent_message_id=parent.id if parent else None,
    )
    # Must sit in the same transaction as the INSERT: room creation and
    # touch_room commit, releasing any lock taken earlier. create_message
    # commits just below, so this is the lock that holds until the row lands.
    if room.group_id is not None and not is_group_id_published(
        db=db, group_id=room.group_id, for_update=True
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NOT_FOUND)
    message = create_message(db=db, message=message)
    message.sender = user
    touch_room(db=db, room=room)
    dto = build_message_dto(message, viewer_id=user.id)
    enqueue_chat_message_notification(message.id)
    return dto


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
        reactions_map = get_reactions_map(
            db=db, message_ids=[message.id for message in messages]
        )
        return ChatMessagesResponse(
            messages=[
                build_message_dto(
                    message,
                    reactions=reactions_map.get(message.id),
                    viewer_id=user.id,
                )
                for message in messages
            ],
            skip=skip,
            limit=limit,
            total=total,
        )


def delete_message_service(room_id: UUID, message_id: UUID, user: Users) -> str:
    """Soft-delete the message and return its deleted_at, so the caller can
    broadcast a matching timestamp to the room."""
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

        deleted_at = soft_delete_message(db=db, message=message)
        return deleted_at.isoformat()


def _get_room_message_or_404(
    db: Session, room_id: UUID, message_id: UUID, user: Users
) -> ChatMessage:
    _get_room_or_404(db=db, room_id=room_id)
    _require_active_member(db=db, room_id=room_id, user_id=user.id)
    message = get_message_by_id(db=db, message_id=message_id, room_id=room_id)
    if not message:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NOT_FOUND)
    return message


def add_message_reaction_service(
    room_id: UUID,
    message_id: UUID,
    user: Users,
    emoji: str,
) -> List[ChatMessageReactionDTO]:
    """Add an emoji reaction to a message (idempotent). Returns the message's
    updated reaction summary."""
    with SessionLocal() as db:
        message = _get_room_message_or_404(
            db=db, room_id=room_id, message_id=message_id, user=user
        )

        existing = get_reaction(db=db, message_id=message.id, user_id=user.id, emoji=emoji)
        if not existing:
            try:
                add_reaction(
                    db=db,
                    reaction=ChatMessageReaction(
                        message_id=message.id,
                        user_id=user.id,
                        emoji=emoji,
                    ),
                )
            except IntegrityError:
                # Concurrent duplicate - the reaction already exists, which is fine
                db.rollback()

        reactions = list_message_reactions(db=db, message_id=message.id)
        return _build_reaction_dtos(reactions, viewer_id=user.id)


def remove_message_reaction_service(
    room_id: UUID,
    message_id: UUID,
    user: Users,
    emoji: str,
) -> List[ChatMessageReactionDTO]:
    """Remove the caller's emoji reaction from a message (idempotent). Returns
    the message's updated reaction summary."""
    with SessionLocal() as db:
        message = _get_room_message_or_404(
            db=db, room_id=room_id, message_id=message_id, user=user
        )

        existing = get_reaction(db=db, message_id=message.id, user_id=user.id, emoji=emoji)
        if existing:
            remove_reaction(db=db, reaction=existing)

        reactions = list_message_reactions(db=db, message_id=message.id)
        return _build_reaction_dtos(reactions, viewer_id=user.id)


def report_message_service(
    room_id: UUID,
    message_id: UUID,
    user: Users,
    reason: ChatMessageReportReason,
    description: Optional[str] = None,
) -> None:
    """Report a message for moderation. One report per user per message."""
    with SessionLocal() as db:
        message = _get_room_message_or_404(
            db=db, room_id=room_id, message_id=message_id, user=user
        )

        if message.sender_id == user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=_CANNOT_REPORT_OWN_MESSAGE,
            )

        existing = get_report_by_message_and_reporter(
            db=db, message_id=message.id, reporter_id=user.id
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=_ALREADY_REPORTED,
            )

        try:
            create_report(
                db=db,
                report=ChatMessageReport(
                    message_id=message.id,
                    reporter_id=user.id,
                    reported_user_id=message.sender_id,
                    room_id=message.room_id,
                    source=ChatMessageReportSource.MANUAL.value,
                    reason=reason.value,
                    description=description,
                ),
            )
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=_ALREADY_REPORTED,
            )
