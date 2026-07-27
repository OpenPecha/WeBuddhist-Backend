from datetime import datetime
import datetime as dt
from uuid import uuid4

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Text,
    text as sql_text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from pecha_api.db.database import Base

FK_GROUP_POSTS_ID = "group_posts.id"
FK_USERS_ID = "users.id"


class GroupPostComment(Base):
    __tablename__ = "group_post_comments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    post_id = Column(
        UUID(as_uuid=True),
        ForeignKey(FK_GROUP_POSTS_ID, ondelete="CASCADE"),
        nullable=False,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey(FK_USERS_ID, ondelete="CASCADE"),
        nullable=False,
    )
    text = Column(Text, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(dt.timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(dt.timezone.utc),
        nullable=True,
    )
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    post = relationship("GroupPost")
    user = relationship("Users")

    __table_args__ = (
        Index("idx_group_post_comments_post_id", "post_id"),
        Index("idx_group_post_comments_user_id", "user_id"),
        Index(
            "idx_group_post_comments_feed",
            "post_id",
            "created_at",
            "id",
            postgresql_where=sql_text("deleted_at IS NULL"),
        ),
    )
