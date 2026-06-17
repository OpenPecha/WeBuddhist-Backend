from uuid import uuid4

from sqlalchemy import Column, String, Text, UUID, ForeignKey
from sqlalchemy.orm import relationship

from ..db.database import Base
from ..plans.plans_enums import LanguageCodeEnum


class AccumulatorMetadata(Base):
    """Per-language name/description for an accumulator. The chosen mala image
    lives on the accumulator itself (one image per accumulator), not here."""
    __tablename__ = "accumulator_metadata"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    accumulator_id = Column(
        UUID(as_uuid=True),
        ForeignKey("accumulators.id", ondelete="CASCADE"),
        nullable=False,
    )
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    language = Column(LanguageCodeEnum, nullable=False)

    accumulator = relationship("Accumulator", back_populates="metadata_entries")
