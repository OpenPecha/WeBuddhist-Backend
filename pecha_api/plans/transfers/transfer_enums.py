import enum

from sqlalchemy import Enum


class TransferEntityType(enum.Enum):
    PLAN = "plan"
    SERIES = "series"


class ContentTransferStatus(enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"


TransferEntityTypeEnum = Enum(
    TransferEntityType,
    name="transfer_entity_type",
    values_callable=lambda enum_cls: [member.value for member in enum_cls],
)
ContentTransferStatusEnum = Enum(ContentTransferStatus, name="content_transfer_status")

NOTIFICATION_CATEGORY_CONTENT_TRANSFER = "content_transfer_incoming"


def normalize_transfer_status(raw) -> ContentTransferStatus:
    if isinstance(raw, ContentTransferStatus):
        return raw
    return ContentTransferStatus(raw)
