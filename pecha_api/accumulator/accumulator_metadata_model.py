from uuid import uuid4

from sqlalchemy import Column, String, Text, UUID, ForeignKey
from sqlalchemy.orm import relationship

from ..db.database import Base
from ..plans.plans_enums import LanguageCodeEnum


class AccumulatorMetadata(Base):
    """Per-language name/description for an accumulator, plus the chosen mala
    image (a reference into the mala_images catalog)."""
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
    mala_image = Column(
        UUID(as_uuid=True),
        ForeignKey("mala_images.id", ondelete="SET NULL"),
        nullable=True,
    )

    accumulator = relationship("Accumulator", back_populates="metadata_entries")
    mala = relationship("MalaImage")
