from sqlalchemy import Column, Index, String, UniqueConstraint, Integer
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from pecha_api.db.database import Base


class UserRecitations(Base):
    __tablename__ = "user_recitations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    text_id = Column(String(255), nullable=False)
    display_order = Column(Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "text_id", name="uq_user_recitations_user_text"),
        Index("idx_user_recitations_user_text_user", "user_id"),
        Index("idx_user_recitations_user_text_text", "text_id"),
    )