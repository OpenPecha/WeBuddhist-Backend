from sqlalchemy import Column, DateTime, UUID, Index, Integer, ForeignKey, String
from sqlalchemy.orm import relationship
from ..db.database import Base
from uuid import uuid4
import _datetime
from _datetime import datetime
from .accumulator_enums import AccumulatorTypeEnum


class Accumulator(Base):
    __tablename__ = "accumulators"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=True)
    group_id = Column(UUID(as_uuid=True), nullable=True)
    # For a user-created accumulator, the preset it was created from. Presets
    # themselves have no parent (NULL).
    parent_id = Column(
        UUID(as_uuid=True),
        ForeignKey("accumulators.id", ondelete="SET NULL"),
        nullable=True,
    )
    type = Column(AccumulatorTypeEnum, nullable=False)
    target_count = Column(Integer, nullable=True)
    current_count = Column(Integer, nullable=False, default=0)
    # Not UUID-only: can hold an external (pecha-style) text id too, not just
    # an internal Text UUID.
    text_id = Column(String(255), nullable=True)
    mantra_id = Column(
        UUID(as_uuid=True),
        ForeignKey("mantra.id", ondelete="SET NULL"),
        nullable=True,
    )
    # The chosen mala image for this accumulator (one per accumulator, not
    # per-language). Defaults from the mantra at create time; the user can
    # override it via the update-mala-image endpoint.
    mala_image = Column(
        UUID(as_uuid=True),
        ForeignKey("mala_images.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(_datetime.timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(_datetime.timezone.utc), onupdate=lambda: datetime.now(_datetime.timezone.utc))
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    metadata_entries = relationship(
        "AccumulatorMetadata",
        back_populates="accumulator",
        cascade="all, delete-orphan",
    )

    mala = relationship("MalaImage")

    __table_args__ = (
        Index("idx_accumulators_user_id", "user_id"),
        Index("idx_accumulators_type", "type"),
        Index("idx_accumulators_parent_id", "parent_id"),
    )
