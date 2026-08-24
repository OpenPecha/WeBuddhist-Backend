from typing import List
from uuid import UUID

from pydantic import BaseModel


class EventPushDeviceTargetDTO(BaseModel):
    id: UUID
    token: str
    platform: str


class EventNotificationRecipientDTO(BaseModel):
    user_id: UUID
    push_devices: List[EventPushDeviceTargetDTO]


class EventNotificationTargetsResponse(BaseModel):
    event_id: UUID
    group_id: UUID
    author_id: UUID
    title: str
    body: str
    recipients: List[EventNotificationRecipientDTO]
    skip: int
    limit: int
    total: int
    has_more: bool
