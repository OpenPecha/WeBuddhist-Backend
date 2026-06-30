from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class PushDeviceTargetDTO(BaseModel):
    token: str
    platform: str


class NotificationContentDTO(BaseModel):
    title: str
    body: str
    custom_image_url: str | None = None


class RoutineNotificationUserTargetDTO(BaseModel):
    user_id: UUID
    notification: NotificationContentDTO
    push_devices: list[PushDeviceTargetDTO]


class RoutineNotificationGroupDTO(BaseModel):
    session_type: str
    source_id: UUID | None
    source_image_url: str | None = None
    users: list[RoutineNotificationUserTargetDTO]


class RoutineNotificationTargetsResponse(BaseModel):
    generated_at: datetime
    matched_time_utc: str
    groups: list[RoutineNotificationGroupDTO]
