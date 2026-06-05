from sqlalchemy import Column, String, DateTime, Boolean, UUID, Index, text, ForeignKey
from sqlalchemy.orm import relationship
from pecha_api.db.database import Base
from pecha_api.plans.plans_enums import PlanStatusEnum
from uuid import uuid4
import _datetime
from _datetime import datetime


class Series(Base):
    __tablename__ = "series"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    image = Column(String(1000), nullable=True)
    author_id = Column(UUID(as_uuid=True), ForeignKey('authors.id', ondelete='RESTRICT'), nullable=False)
    group_id = Column(UUID(as_uuid=True), ForeignKey('author_groups.id', ondelete='RESTRICT'), nullable=False)
    featured = Column(Boolean, default=False, nullable=False)
    status = Column(PlanStatusEnum, nullable=False, default='DRAFT')
    
    created_at = Column(DateTime(timezone=True), default=datetime.now(_datetime.timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.now(_datetime.timezone.utc))
    updated_by = Column(String(255))
    
    deleted_at = Column(DateTime(timezone=True))
    deleted_by = Column(String(255))

    author = relationship("Author", backref="series", passive_deletes=True)
    plans = relationship("Plan", back_populates="series")
    metadata_entries = relationship(
        "SeriesMetadata",
        back_populates="series",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_series_featured", "featured", postgresql_where=text("featured = TRUE")),
        Index("idx_series_status", "status"),
    )
