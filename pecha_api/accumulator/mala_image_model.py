from uuid import uuid4

from sqlalchemy import Column, String, Boolean, UUID

from ..db.database import Base


class MalaImage(Base):
    """Catalog of selectable mala images. The app lists these and the user
    picks one per accumulator (stored on accumulators.mala_image)."""
    __tablename__ = "mala_images"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    url = Column(String(1000), nullable=False)
    name = Column(String(255), nullable=True)
    default = Column(Boolean, nullable=False, default=False)
