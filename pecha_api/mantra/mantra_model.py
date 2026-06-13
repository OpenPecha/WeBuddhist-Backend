from sqlalchemy import Column, String, DateTime, UUID
from sqlalchemy.orm import relationship
from ..db.database import Base
from uuid import uuid4
import _datetime
from _datetime import datetime


class Mantra(Base):
    __tablename__ = "mantra"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    audio_url = Column(String(1000), nullable=True)

    created_at = Column(DateTime(timezone=True), default=datetime.now(_datetime.timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.now(_datetime.timezone.utc))

    metadata_entries = relationship(
        "MantraMetadata",
        back_populates="mantra",
        cascade="all, delete-orphan",
    )
