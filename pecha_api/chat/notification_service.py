from uuid import UUID

from fastapi import HTTPException
from starlette import status

from pecha_api.chat.notification_repository import (
    deactivate_push_device_token_by_id,
    get_active_push_devices_by_user_ids,
    get_sender_display_name,
    list_group_chat_recipient_user_ids,
    list_private_chat_recipient_user_ids,
    normalize_platform,
)
from pecha_api.chat.notification_response_models import (
    ChatNotificationRecipientDTO,
    ChatNotificationTargetsResponse,
    ChatPushDeviceTargetDTO,
    DeactivatePushDeviceResponse,
)
from pecha_api.chat.repository import get_message_by_id_any_room
from pecha_api.config import get_int
from pecha_api.db.database import SessionLocal
from pecha_api.plans.response_message import NOT_FOUND


def _preview_body(body: str, max_length: int) -> str:
    text = " ".join(body.split())
    if len(text) <= max_length:
        return text
    return text[: max(max_length - 1, 1)].rstrip() + "…"


def _build_notification_copy(
    *,
    chat_kind: str,
    room_name: str,
    sender_name: str,
    message_body: str,
) -> tuple[str, str]:
    preview = _preview_body(
        message_body,
        max(get_int("CHAT_NOTIFICATION_PREVIEW_MAX_LENGTH"), 1),
    )
    if chat_kind == "PRIVATE":
        return sender_name, preview
    return room_name, f"{sender_name}: {preview}"


def get_chat_notification_targets(
    *,
    message_id: UUID,
    skip: int = 0,
    limit: int = 100,
) -> ChatNotificationTargetsResponse:
    if skip < 0:
        skip = 0
    if limit < 1:
        limit = 1
    if limit > 500:
        limit = 500

    with SessionLocal() as db:
        message = get_message_by_id_any_room(db=db, message_id=message_id)
        if not message or not message.room:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NOT_FOUND)

        room = message.room
        chat_kind = "GROUP" if room.group_id is not None else "PRIVATE"
        sender_name = get_sender_display_name(db=db, sender_id=message.sender_id)
        title, body = _build_notification_copy(
            chat_kind=chat_kind,
            room_name=room.name,
            sender_name=sender_name,
            message_body=message.body,
        )

        if chat_kind == "PRIVATE":
            all_recipient_ids = list_private_chat_recipient_user_ids(
                room=room,
                sender_id=message.sender_id,
            )
            total = len(all_recipient_ids)
            recipient_ids = all_recipient_ids[skip : skip + limit]
        else:
            recipient_ids, total = list_group_chat_recipient_user_ids(
                db=db,
                group_id=room.group_id,
                sender_id=message.sender_id,
                skip=skip,
                limit=limit,
            )

        devices_by_user = get_active_push_devices_by_user_ids(db=db, user_ids=recipient_ids)
        recipients: list[ChatNotificationRecipientDTO] = []
        for user_id in recipient_ids:
            devices = devices_by_user.get(user_id) or []
            if not devices:
                continue
            recipients.append(
                ChatNotificationRecipientDTO(
                    user_id=user_id,
                    push_devices=[
                        ChatPushDeviceTargetDTO(
                            id=device.id,
                            token=device.token,
                            platform=normalize_platform(device.platform),
                        )
                        for device in devices
                    ],
                )
            )

        return ChatNotificationTargetsResponse(
            message_id=message.id,
            room_id=room.id,
            sender_id=message.sender_id,
            chat_kind=chat_kind,
            group_id=room.group_id,
            title=title,
            body=body,
            recipients=recipients,
            skip=skip,
            limit=limit,
            total=total,
            has_more=(skip + limit) < total,
        )


def deactivate_push_device_service(*, push_device_id: UUID) -> DeactivatePushDeviceResponse:
    with SessionLocal() as db:
        device = deactivate_push_device_token_by_id(db=db, push_device_id=push_device_id)
        if not device:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=NOT_FOUND)
        return DeactivatePushDeviceResponse(
            push_device_id=device.id,
            deactivated=not device.is_active,
        )
