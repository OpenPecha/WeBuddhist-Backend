import datetime as _datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from pecha_api.db.database import Base
from pecha_api.region_restrictions.region_restriction_enums import RestrictedItemTypeEnum


class ChinaRestrictedItem(Base):
    __tablename__ = "china_restricted_items"
    __table_args__ = (
        UniqueConstraint(
            "item_type",
            "item_id",
            name="uq_china_restricted_items_type_id",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    item_type = Column(RestrictedItemTypeEnum, nullable=False)
    item_id = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=_datetime.datetime.now(_datetime.timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=_datetime.datetime.now(_datetime.timezone.utc),
        onupdate=_datetime.datetime.now(_datetime.timezone.utc),
    )
