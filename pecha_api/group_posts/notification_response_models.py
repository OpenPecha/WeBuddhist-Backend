from typing import List
from uuid import UUID

from pydantic import BaseModel


class GroupPostPushDeviceTargetDTO(BaseModel):
    id: UUID
    token: str
    platform: str


class GroupPostNotificationRecipientDTO(BaseModel):
    user_id: UUID
    push_devices: List[GroupPostPushDeviceTargetDTO]


class GroupPostNotificationTargetsResponse(BaseModel):
    post_id: UUID
    group_id: UUID
    author_id: UUID
    title: str
    body: str
    recipients: List[GroupPostNotificationRecipientDTO]
    skip: int
    limit: int
    total: int
    has_more: bool
