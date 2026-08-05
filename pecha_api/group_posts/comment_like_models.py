from datetime import datetime
import datetime as dt
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from pecha_api.db.database import Base

FK_GROUP_POST_COMMENTS_ID = "group_post_comments.id"
FK_USERS_ID = "users.id"


class GroupPostCommentLike(Base):
    __tablename__ = "group_post_comment_likes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    comment_id = Column(
        UUID(as_uuid=True),
        ForeignKey(FK_GROUP_POST_COMMENTS_ID, ondelete="CASCADE"),
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

    comment = relationship("GroupPostComment")
    user = relationship("Users")

    __table_args__ = (
        UniqueConstraint("comment_id", "user_id", name="uq_group_post_comment_likes_comment_user"),
        Index("idx_group_post_comment_likes_comment_id", "comment_id"),
        Index("idx_group_post_comment_likes_user_id", "user_id"),
        Index(
            "idx_group_post_comment_likes_comment_created",
            "comment_id",
            "created_at",
            "id",
        ),
    )
