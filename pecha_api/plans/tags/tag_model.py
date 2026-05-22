from sqlalchemy import Column, String, DateTime, Text, UUID, ForeignKey, Table, Index, text
from sqlalchemy.orm import relationship
from uuid import uuid4
import _datetime
from _datetime import datetime

from pecha_api.db.database import Base

plan_tags = Table(
    "plan_tags",
    Base.metadata,
    Column("plan_id", UUID(as_uuid=True), ForeignKey("plans.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", UUID(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class Tag(Base):
    __tablename__ = "tags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    image_key = Column(String(1000), nullable=True)
    description = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=datetime.now(_datetime.timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.now(_datetime.timezone.utc))
    updated_by = Column(String(255))
    deleted_at = Column(DateTime(timezone=True))
    deleted_by = Column(String(255))

    plans = relationship("Plan", secondary=plan_tags, back_populates="tag_list")

    __table_args__ = (
        Index(
            "idx_tags_name_unique",
            "name",
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )
