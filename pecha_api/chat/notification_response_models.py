from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ChatPushDeviceTargetDTO(BaseModel):
    id: UUID
    token: str
    platform: str


class ChatNotificationRecipientDTO(BaseModel):
    user_id: UUID
    push_devices: List[ChatPushDeviceTargetDTO]


class ChatNotificationTargetsResponse(BaseModel):
    message_id: UUID
    room_id: UUID
    sender_id: UUID
    chat_kind: str
    group_id: Optional[UUID] = None
    title: str
    body: str
    recipients: List[ChatNotificationRecipientDTO]
    skip: int
    limit: int
    total: int
    has_more: bool


class DeactivatePushDeviceRequest(BaseModel):
    push_device_id: UUID = Field(..., description="Push device token record ID to deactivate")


class DeactivatePushDeviceResponse(BaseModel):
    push_device_id: UUID
    deactivated: bool
