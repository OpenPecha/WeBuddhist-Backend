from sqlalchemy import Column, String, DateTime, UUID, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from ..db.database import Base
from uuid import uuid4
import _datetime
from _datetime import datetime


class VerseMetadata(Base):
    __tablename__ = "verse_metadata"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    verse_of_day_id = Column(UUID(as_uuid=True), ForeignKey('verse_of_day.id', ondelete='CASCADE'), nullable=False)
    verse = Column(JSONB, nullable=False)
    lang = Column(String(10), nullable=False)

    created_at = Column(DateTime(timezone=True), default=datetime.now(_datetime.timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.now(_datetime.timezone.utc))

    verse_of_day = relationship("VerseOfDay", back_populates="verse_metadata")

    __table_args__ = (
        Index("idx_verse_metadata_verse_of_day_id", "verse_of_day_id"),
        Index("idx_verse_metadata_lang", "lang"),
        UniqueConstraint("verse_of_day_id", "lang", name="uq_verse_metadata_verse_of_day_lang"),
    )
