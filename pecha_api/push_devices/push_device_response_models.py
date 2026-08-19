from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, field_validator

from pecha_api.push_devices.push_device_enums import PushPlatform


class RegisterPushDeviceRequest(BaseModel):
    token: str
    platform: PushPlatform
    device_id: Optional[str] = None

    @field_validator("token")
    @classmethod
    def _validate_token(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("token must not be empty")
        return value

    @field_validator("device_id")
    @classmethod
    def _validate_device_id(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("device_id must not be empty when provided")
        return value


class PushDeviceTokenDTO(BaseModel):
    id: UUID
    platform: PushPlatform
    device_id: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class PushDeviceTokensResponse(BaseModel):
    devices: List[PushDeviceTokenDTO]


class AdminPushDeviceTokenDTO(BaseModel):
    id: UUID
    user_id: UUID
    token: str
    platform: PushPlatform
    device_id: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class AdminPushDeviceTokensListResponse(BaseModel):
    devices: List[AdminPushDeviceTokenDTO]
    total: int
    skip: int
    limit: int
