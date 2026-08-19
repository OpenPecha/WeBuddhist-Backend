from datetime import datetime
import datetime as dt
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from pecha_api.db.database import Base

FK_GROUP_POSTS_ID = "group_posts.id"
FK_USERS_ID = "users.id"


class GroupPostLike(Base):
    __tablename__ = "group_post_likes"

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
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(dt.timezone.utc),
        nullable=False,
    )

    post = relationship("GroupPost")
    user = relationship("Users")

    __table_args__ = (
        UniqueConstraint("post_id", "user_id", name="uq_group_post_likes_post_user"),
        Index("idx_group_post_likes_post_id", "post_id"),
        Index("idx_group_post_likes_user_id", "user_id"),
        Index(
            "idx_group_post_likes_post_created",
            "post_id",
            "created_at",
            "id",
        ),
    )
