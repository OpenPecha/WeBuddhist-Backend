from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel

from pecha_api.plans.transfers.transfer_enums import ContentTransferStatus, TransferEntityType


class CreateTransferRequestBody(BaseModel):
    target_group_id: UUID


class TransferRequestDTO(BaseModel):
    id: UUID
    entity_type: TransferEntityType
    entity_id: UUID
    from_group_id: UUID
    to_group_id: UUID
    status: ContentTransferStatus
    requested_by: str
    expires_at: datetime
    created_at: datetime
    entity_title: Optional[str] = None
    from_group_title: Optional[str] = None
    to_group_title: Optional[str] = None


class TransferRequestListResponse(BaseModel):
    transfers: List[TransferRequestDTO]
    total: int


class TransferRequestCreatedResponse(BaseModel):
    transfer: TransferRequestDTO
    notification_id: Optional[UUID] = None
