from datetime import datetime
import datetime as dt
from uuid import uuid4

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from pecha_api.db.database import Base

from .enums import GroupPostMediaTypeEnum, GroupPostStatusEnum

FK_AUTHOR_GROUPS_ID = "author_groups.id"
FK_GROUP_POSTS_ID = "group_posts.id"
CASCADE_DELETE_ORPHAN = "all, delete-orphan"


class GroupPost(Base):
    __tablename__ = "group_posts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    group_id = Column(
        UUID(as_uuid=True),
        ForeignKey(FK_AUTHOR_GROUPS_ID, ondelete="CASCADE"),
        nullable=False,
    )
    caption = Column(Text, nullable=True)
    status = Column(GroupPostStatusEnum, nullable=False, default="PUBLISHED")
    published_at = Column(DateTime(timezone=True), nullable=False)

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

    created_by = Column(String(255), nullable=False)
    updated_by = Column(String(255), nullable=True)
    deleted_by = Column(String(255), nullable=True)

    media = relationship(
        "GroupPostMedia",
        back_populates="post",
        cascade=CASCADE_DELETE_ORPHAN,
        order_by="GroupPostMedia.display_order",
    )
    links = relationship(
        "GroupPostLink",
        back_populates="post",
        cascade=CASCADE_DELETE_ORPHAN,
        order_by="GroupPostLink.display_order",
    )

    __table_args__ = (
        Index("idx_group_posts_group_id", "group_id"),
        Index(
            "idx_group_posts_feed",
            "group_id",
            text("published_at DESC"),
            text("id DESC"),
            postgresql_where=text("deleted_at IS NULL AND status = 'PUBLISHED'"),
        ),
    )


class GroupPostMedia(Base):
    __tablename__ = "group_post_media"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    post_id = Column(
        UUID(as_uuid=True),
        ForeignKey(FK_GROUP_POSTS_ID, ondelete="CASCADE"),
        nullable=False,
    )
    media_type = Column(GroupPostMediaTypeEnum, nullable=False)
    media_key = Column(String(1000), nullable=False)
    thumbnail_key = Column(String(1000), nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    display_order = Column(Integer, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(dt.timezone.utc),
        nullable=False,
    )

    post = relationship("GroupPost", back_populates="media")

    __table_args__ = (
        UniqueConstraint("post_id", "display_order", name="uq_group_post_media_post_order"),
        Index("idx_group_post_media_post_id", "post_id"),
    )


class GroupPostLink(Base):
    __tablename__ = "group_post_links"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    post_id = Column(
        UUID(as_uuid=True),
        ForeignKey(FK_GROUP_POSTS_ID, ondelete="CASCADE"),
        nullable=False,
    )
    type = Column(String(50), nullable=False)
    url = Column(String(2000), nullable=False)
    label = Column(String(255), nullable=True)
    display_order = Column(Integer, nullable=False, default=1)

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

    post = relationship("GroupPost", back_populates="links")

    __table_args__ = (
        Index("idx_group_post_links_post_id", "post_id"),
    )
