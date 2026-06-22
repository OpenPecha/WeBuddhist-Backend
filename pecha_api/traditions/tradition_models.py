from uuid import uuid4
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, UUID, Index, String, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from ..db.database import Base
from ..plans.plans_enums import LanguageCodeEnum


class Tradition(Base):
    """A node in the Buddhist tradition taxonomy. The hierarchy is self
    referential via ``parent_id`` (a level-1 root has ``parent_id`` NULL).
    Per-language names live in ``tradition_metadata`` (one row per language)."""
    __tablename__ = "tradition_list"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    parent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tradition_list.id", ondelete="SET NULL"),
        nullable=True,
    )
    # List of region strings, e.g. ["Tibet", "Bhutan", "Nepal"].
    regions = Column(JSONB, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    parent = relationship("Tradition", remote_side=[id], backref="children")
    metadata_entries = relationship(
        "TraditionMetadata",
        back_populates="tradition",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_tradition_list_parent_id", "parent_id"),
    )


class TraditionMetadata(Base):
    """Per-language display name and aliases for a tradition. One row per
    (tradition, language). ``other_names`` holds the list of aliases for that
    language."""
    __tablename__ = "tradition_metadata"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tradition_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tradition_list.id", ondelete="CASCADE"),
        nullable=False,
    )
    language = Column(LanguageCodeEnum, nullable=False)
    name = Column(String(255), nullable=False)
    # List of alias strings for this language.
    other_names = Column(JSONB, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    tradition = relationship("Tradition", back_populates="metadata_entries")

    __table_args__ = (
        UniqueConstraint("tradition_id", "language", name="uq_tradition_metadata_tradition_language"),
        Index("idx_tradition_metadata_language", "language"),
    )
