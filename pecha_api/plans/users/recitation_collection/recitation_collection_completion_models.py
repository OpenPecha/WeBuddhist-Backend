from datetime import datetime
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


class RecitationCollectionChantCompletion(Base):
    __tablename__ = "recitation_collection_chant_completions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    chant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("recitation_collection_items.id", ondelete="CASCADE"),
        nullable=False,
    )
    collection_id = Column(
        UUID(as_uuid=True),
        ForeignKey("recitation_collections.id", ondelete="CASCADE"),
        nullable=False,
    )
    completion_date = Column(Date, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(dt.timezone.utc),
        nullable=False,
    )

    user = relationship("Users")
    chant_item = relationship("RecitationCollectionItem")
    collection = relationship("RecitationCollection")

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "chant_id",
            "completion_date",
            name="uq_recitation_collection_chant_completion_user_chant_date",
        ),
        Index(
            "idx_recitation_collection_chant_completion_user_date",
            "user_id",
            "completion_date",
        ),
        Index(
            "idx_recitation_collection_chant_completion_collection",
            "collection_id",
        ),
    )
