from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from pecha_api.plans.transfers.transfer_enums import ContentTransferStatus, TransferEntityType
from pecha_api.plans.transfers.transfer_models import ContentTransferRequest


def _transfer_expires_at() -> datetime:
    from pecha_api.config import get_int

    minutes = get_int("GROUP_INVITE_EXPIRY_MINUTES")
    minutes = max(1, min(minutes, 24 * 60))
    return datetime.now(timezone.utc) + timedelta(minutes=minutes)


def create_transfer_request(
    db: Session,
    *,
    entity_type: TransferEntityType,
    entity_id: UUID,
    from_group_id: UUID,
    to_group_id: UUID,
    requested_by: str,
) -> ContentTransferRequest:
    row = ContentTransferRequest(
        entity_type=entity_type,
        entity_id=entity_id,
        from_group_id=from_group_id,
        to_group_id=to_group_id,
        status=ContentTransferStatus.PENDING,
        requested_by=requested_by,
        expires_at=_transfer_expires_at(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_transfer_by_id(db: Session, transfer_id: UUID) -> Optional[ContentTransferRequest]:
    return db.query(ContentTransferRequest).filter(ContentTransferRequest.id == transfer_id).first()


def has_pending_transfer(
    db: Session,
    *,
    entity_type: TransferEntityType,
    entity_id: UUID,
) -> bool:
    return (
        db.query(ContentTransferRequest.id)
        .filter(
            ContentTransferRequest.entity_type == entity_type,
            ContentTransferRequest.entity_id == entity_id,
            ContentTransferRequest.status == ContentTransferStatus.PENDING,
        )
        .first()
        is not None
    )


def list_incoming_transfers(
    db: Session,
    *,
    group_ids: List[UUID],
    status: Optional[ContentTransferStatus] = None,
) -> List[ContentTransferRequest]:
    if not group_ids:
        return []
    query = db.query(ContentTransferRequest).filter(
        ContentTransferRequest.to_group_id.in_(group_ids)
    )
    if status is not None:
        query = query.filter(ContentTransferRequest.status == status.value)
    return query.order_by(ContentTransferRequest.created_at.desc()).all()


def list_outgoing_transfers(
    db: Session,
    *,
    group_ids: List[UUID],
    status: Optional[ContentTransferStatus] = None,
) -> List[ContentTransferRequest]:
    if not group_ids:
        return []
    query = db.query(ContentTransferRequest).filter(
        ContentTransferRequest.from_group_id.in_(group_ids)
    )
    if status is not None:
        query = query.filter(ContentTransferRequest.status == status.value)
    return query.order_by(ContentTransferRequest.created_at.desc()).all()


def save_transfer(db: Session, transfer: ContentTransferRequest) -> ContentTransferRequest:
    db.add(transfer)
    db.commit()
    db.refresh(transfer)
    return transfer
