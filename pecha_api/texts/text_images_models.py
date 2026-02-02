import _datetime
from _datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, String, DateTime, UUID, Index

from pecha_api.db.database import Base


class TextImage(Base):
    __tablename__ = "text_images"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    text_id = Column(String(255), nullable=False, index=True)
    image_url = Column(String(1000), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.now(_datetime.timezone.utc), nullable=False)

    __table_args__ = (
        Index("idx_text_images_text_id", "text_id"),
    )
