import datetime as _datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, String, UniqueConstraint
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
    # Holds both real UUIDs (plans, series, accumulators, etc.) and, for
    # RECITATION, external OpenPecha-style string text ids stored as text.
    item_id = Column(String(255), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: _datetime.datetime.now(_datetime.timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: _datetime.datetime.now(_datetime.timezone.utc),
        onupdate=lambda: _datetime.datetime.now(_datetime.timezone.utc),
    )
