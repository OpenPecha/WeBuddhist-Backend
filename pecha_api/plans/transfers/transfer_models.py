from uuid import uuid4
import _datetime
from _datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, String, UUID

from pecha_api.db.database import Base
from pecha_api.plans.transfers.transfer_enums import (
    ContentTransferStatusEnum,
    TransferEntityTypeEnum,
)


class ContentTransferRequest(Base):
    __tablename__ = "content_transfer_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    entity_type = Column(TransferEntityTypeEnum, nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=False)
    from_group_id = Column(
        UUID(as_uuid=True),
        ForeignKey("author_groups.id", ondelete="CASCADE"),
        nullable=False,
    )
    to_group_id = Column(
        UUID(as_uuid=True),
        ForeignKey("author_groups.id", ondelete="CASCADE"),
        nullable=False,
    )
    status = Column(ContentTransferStatusEnum, nullable=False, default="PENDING")
    requested_by = Column(String(255), nullable=False)
    responded_by = Column(String(255), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=datetime.now(_datetime.timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        Index("idx_content_transfer_to_group_status", "to_group_id", "status"),
        Index("idx_content_transfer_entity_status", "entity_type", "entity_id", "status"),
    )
