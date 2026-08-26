from sqlalchemy import Column, String, DateTime, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from datetime import datetime, timezone
from pecha_api.db.database import Base
from pecha_api.bookmarks.bookmark_enums import BookmarkTypeEnum


class Bookmark(Base):
    __tablename__ = "bookmarks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    type = Column(BookmarkTypeEnum, nullable=False)
    source_id = Column(String(255), nullable=False)
    name = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("user_id", "type", "source_id", name="uq_bookmarks_user_type_source"),
        Index("idx_bookmarks_user_id", "user_id"),
        Index("idx_bookmarks_type", "type"),
    )
