from uuid import uuid4

from sqlalchemy import Column, String, Text, UUID, ForeignKey
from sqlalchemy.orm import relationship

from pecha_api.db.database import Base
from pecha_api.plans.plans_enums import LanguageCodeEnum


class SeriesMetadata(Base):
    __tablename__ = "series_metadata"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    language = Column(LanguageCodeEnum, nullable=False)
    series_id = Column(
        UUID(as_uuid=True),
        ForeignKey("series.id", ondelete="CASCADE"),
        nullable=False,
    )

    series = relationship("Series", back_populates="metadata_entries")