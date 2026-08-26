from uuid import uuid4

from sqlalchemy import Column, String, Text, UUID, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship

from pecha_api.db.database import Base
from pecha_api.plans.plans_enums import LanguageCodeEnum


class TagMetadata(Base):
    __tablename__ = "tag_metadata"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tag_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tags.id", ondelete="CASCADE"),
        nullable=False,
    )
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    language = Column(LanguageCodeEnum, nullable=False)

    tag = relationship("Tag", back_populates="metadata_entries")

    __table_args__ = (
        UniqueConstraint("tag_id", "language", name="uq_tag_metadata_tag_language"),
        Index("idx_tag_metadata_tag_language", "tag_id", "language"),
    )
