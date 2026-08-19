from datetime import datetime, date
import datetime as dt
from uuid import uuid4

from sqlalchemy import (
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from pecha_api.db.database import Base


class UserChantCompletion(Base):
    __tablename__ = "user_chant_completion"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    chant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("group_recitation_collection_items.id", ondelete="CASCADE"),
        nullable=False,
    )
    chant_collection_id = Column(
        UUID(as_uuid=True),
        ForeignKey("group_recitation_collections.id", ondelete="CASCADE"),
        nullable=False,
    )
    completion_date = Column(Date, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(dt.timezone.utc),
        nullable=False,
    )

    user = relationship("Users")
    chant_item = relationship("GroupRecitationCollectionItem")
    chant_collection = relationship("GroupRecitationCollection")

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "chant_id",
            "completion_date",
            name="uq_user_chant_completion_user_chant_date",
        ),
        Index("idx_user_chant_completion_user_date", "user_id", "completion_date"),
        Index("idx_user_chant_completion_collection", "chant_collection_id"),
    )
