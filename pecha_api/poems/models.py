from datetime import datetime
import datetime as dt
from uuid import uuid4

from sqlalchemy import Column, DateTime, Index, String, Text, text
from sqlalchemy.dialects.postgresql import UUID

from pecha_api.db.database import Base

from .enums import PoemStatusEnum


class Poem(Base):
    __tablename__ = "poems"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    author_name = Column(String(255), nullable=False)
    chapter_name = Column(String(255), nullable=True)
    image_key = Column(String(1000), nullable=True)
    status = Column(PoemStatusEnum, nullable=False, default="DRAFT")
    published_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(dt.timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(dt.timezone.utc),
        nullable=False,
    )
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    created_by = Column(String(255), nullable=False)
    updated_by = Column(String(255), nullable=True)

    __table_args__ = (
        Index(
            "idx_poems_feed",
            text("published_at DESC"),
            text("id DESC"),
            postgresql_where=text("deleted_at IS NULL AND status = 'PUBLISHED'"),
        ),
        Index(
            "idx_poems_chapter_name",
            "chapter_name",
            postgresql_where=text("deleted_at IS NULL"),
        ),
        Index(
            "idx_poems_author_name",
            "author_name",
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )
