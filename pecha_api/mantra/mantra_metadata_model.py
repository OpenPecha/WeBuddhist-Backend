from uuid import uuid4

from sqlalchemy import Column, String, Text, UUID, ForeignKey
from sqlalchemy.orm import relationship

from ..db.database import Base
from ..plans.plans_enums import LanguageCodeEnum


class MantraMetadata(Base):
    __tablename__ = "mantra_metadata"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    mantra_id = Column(
        UUID(as_uuid=True),
        ForeignKey("mantra.id", ondelete="CASCADE"),
        nullable=False,
    )
    text = Column(Text, nullable=False)
    meaning = Column(Text, nullable=True)
    transliteration = Column(Text, nullable=True)
    language = Column(LanguageCodeEnum, nullable=False)

    mantra = relationship("Mantra", back_populates="metadata_entries")
