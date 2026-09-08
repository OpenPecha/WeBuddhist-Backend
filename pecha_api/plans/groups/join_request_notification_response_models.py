from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class JoinRequestPushDeviceTargetDTO(BaseModel):
    id: UUID
    token: str
    platform: str


class JoinRequestNotificationRecipientDTO(BaseModel):
    user_id: UUID
    push_devices: List[JoinRequestPushDeviceTargetDTO]


class JoinRequestNotificationTargetsResponse(BaseModel):
    join_request_id: UUID
    group_id: UUID
    event_type: str
    status: str
    group_name: str
    requester_name: str
    title: str
    body: str
    recipients: List[JoinRequestNotificationRecipientDTO]
    skip: int
    limit: int
    total: int
    has_more: bool
