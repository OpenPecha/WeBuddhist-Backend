from datetime import datetime
import datetime as dt
from uuid import uuid4

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from pecha_api.db.database import Base

FK_AUTHOR_GROUPS_ID = "author_groups.id"
FK_GROUP_RECITATION_COLLECTIONS_ID = "group_recitation_collections.id"
CASCADE_DELETE_ORPHAN = "all, delete-orphan"


class GroupRecitationCollection(Base):
    __tablename__ = "group_recitation_collections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    group_id = Column(
        UUID(as_uuid=True),
        ForeignKey(FK_AUTHOR_GROUPS_ID, ondelete="CASCADE"),
        nullable=False,
    )
    name = Column(String(255), nullable=False)
    img_url = Column(String(1000), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(dt.timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(dt.timezone.utc),
        nullable=True,
    )
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    created_by = Column(UUID(as_uuid=True), nullable=False)
    updated_by = Column(UUID(as_uuid=True), nullable=True)

    items = relationship(
        "GroupRecitationCollectionItem",
        back_populates="collection",
        cascade=CASCADE_DELETE_ORPHAN,
    )

    __table_args__ = (
        Index("idx_group_recitation_collections_group_id", "group_id"),
    )


class GroupRecitationCollectionItem(Base):
    __tablename__ = "group_recitation_collection_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    group_recitation_collection_id = Column(
        UUID(as_uuid=True),
        ForeignKey(FK_GROUP_RECITATION_COLLECTIONS_ID, ondelete="CASCADE"),
        nullable=False,
    )
    text_id = Column(UUID(as_uuid=True), nullable=False)
    display_order = Column(Integer, nullable=False)

    deleted_at = Column(DateTime(timezone=True), nullable=True)

    collection = relationship(
        "GroupRecitationCollection",
        back_populates="items",
    )

    __table_args__ = (
        Index(
            "uq_group_recitation_collection_items_collection_text",
            "group_recitation_collection_id",
            "text_id",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index(
            "idx_group_recitation_collection_items_collection_id",
            "group_recitation_collection_id",
        ),
    )
