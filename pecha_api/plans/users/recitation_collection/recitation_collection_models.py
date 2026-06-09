from sqlalchemy import Column, Index, UniqueConstraint, Integer, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from uuid import uuid4
from datetime import datetime
from pecha_api.db.database import Base


class RecitationCollection(Base):
    __tablename__ = "recitation_collections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    name = Column(String(255), nullable=False)
    img_url = Column(String(1000), nullable=False)
    created_at = Column(String, nullable=False, default=lambda: datetime.utcnow().isoformat())
    updated_at = Column(String, nullable=False, default=lambda: datetime.utcnow().isoformat())

    items = relationship("RecitationCollectionItem", back_populates="collection", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_recitation_collections_user_id", "user_id"),
    )


class RecitationCollectionItem(Base):
    __tablename__ = "recitation_collection_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    recitation_collection_id = Column(UUID(as_uuid=True), ForeignKey("recitation_collections.id", ondelete="CASCADE"), nullable=False)
    text_id = Column(UUID(as_uuid=True), nullable=False)
    display_order = Column(Integer, nullable=False)

    collection = relationship("RecitationCollection", back_populates="items")

    __table_args__ = (
        UniqueConstraint("recitation_collection_id", "text_id", name="uq_recitation_collection_items_collection_text"),
        Index("idx_recitation_collection_items_collection_id", "recitation_collection_id"),
    )
