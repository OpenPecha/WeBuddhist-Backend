from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class VerseOfDayPushDeviceTargetDTO(BaseModel):
    token: str
    platform: str


class VerseOfDayNotificationContentDTO(BaseModel):
    title: str
    body: str
    image_url: str | None = None


class VerseOfDayNotificationUserTargetDTO(BaseModel):
    user_id: UUID
    notification: VerseOfDayNotificationContentDTO
    push_devices: list[VerseOfDayPushDeviceTargetDTO]


class VerseOfDayNotificationTargetsResponse(BaseModel):
    generated_at: datetime
    users: list[VerseOfDayNotificationUserTargetDTO]
