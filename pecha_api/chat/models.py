from datetime import datetime
import datetime as dt
from uuid import uuid4

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    text as sql_text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from pecha_api.db.database import Base

from .enums import ChatRoomMemberRoleEnum

FK_AUTHOR_GROUPS_ID = "author_groups.id"
FK_USERS_ID = "users.id"
FK_CHAT_ROOMS_ID = "chat_rooms.id"
FK_CHAT_MESSAGES_ID = "chat_messages.id"
CASCADE_DELETE_ORPHAN = "all, delete-orphan"


class ChatRoom(Base):
    __tablename__ = "chat_rooms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    group_id = Column(
        UUID(as_uuid=True),
        ForeignKey(FK_AUTHOR_GROUPS_ID, ondelete="CASCADE"),
        nullable=True,
    )
    sender_id = Column(
        UUID(as_uuid=True),
        ForeignKey(FK_USERS_ID, ondelete="CASCADE"),
        nullable=True,
    )
    receiver_id = Column(
        UUID(as_uuid=True),
        ForeignKey(FK_USERS_ID, ondelete="CASCADE"),
        nullable=True,
    )
    name = Column(String(255), nullable=False)
    img_url = Column(String(1000), nullable=True)
    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey(FK_USERS_ID),
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(dt.timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(dt.timezone.utc),
        nullable=False,
    )
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    members = relationship(
        "ChatRoomMember",
        back_populates="room",
        cascade=CASCADE_DELETE_ORPHAN,
    )
    messages = relationship(
        "ChatMessage",
        back_populates="room",
        cascade=CASCADE_DELETE_ORPHAN,
    )

    __table_args__ = (
        CheckConstraint(
            "(group_id IS NOT NULL AND sender_id IS NULL AND receiver_id IS NULL) OR "
            "(group_id IS NULL AND sender_id IS NOT NULL AND receiver_id IS NOT NULL AND sender_id <> receiver_id)",
            name="ck_chat_rooms_kind_shape",
        ),
        Index(
            "uq_chat_rooms_group_id",
            "group_id",
            unique=True,
            postgresql_where=sql_text("group_id IS NOT NULL AND deleted_at IS NULL"),
        ),
        Index(
            "uq_chat_rooms_sender_receiver",
            "sender_id",
            "receiver_id",
            unique=True,
            postgresql_where=sql_text("group_id IS NULL AND deleted_at IS NULL"),
        ),
        Index("idx_chat_rooms_updated_at", sql_text("updated_at DESC")),
        Index("idx_chat_rooms_created_by", "created_by"),
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    room_id = Column(
        UUID(as_uuid=True),
        ForeignKey(FK_CHAT_ROOMS_ID, ondelete="CASCADE"),
        nullable=False,
    )
    sender_id = Column(
        UUID(as_uuid=True),
        ForeignKey(FK_USERS_ID, ondelete="CASCADE"),
        nullable=False,
    )
    parent_message_id = Column(
        UUID(as_uuid=True),
        ForeignKey(FK_CHAT_MESSAGES_ID, ondelete="SET NULL"),
        nullable=True,
    )
    body = Column(Text, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(dt.timezone.utc),
        nullable=False,
    )
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    notification_sqs_message_id = Column(String(128), nullable=True)
    notification_dispatched_at = Column(DateTime(timezone=True), nullable=True)

    room = relationship("ChatRoom", back_populates="messages")
    sender = relationship("Users")
    parent = relationship("ChatMessage", remote_side="ChatMessage.id", foreign_keys=[parent_message_id])
    reactions = relationship(
        "ChatMessageReaction",
        back_populates="message",
        cascade=CASCADE_DELETE_ORPHAN,
    )

    __table_args__ = (
        Index("idx_chat_messages_room_created", "room_id", sql_text("created_at DESC")),
        Index(
            "idx_chat_messages_room_active",
            "room_id",
            "created_at",
            postgresql_where=sql_text("deleted_at IS NULL"),
        ),
        Index(
            "idx_chat_messages_undispatched_notifications",
            "created_at",
            postgresql_where=sql_text(
                "deleted_at IS NULL AND notification_sqs_message_id IS NULL"
            ),
        ),
    )


class ChatRoomMember(Base):
    __tablename__ = "chat_room_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    room_id = Column(
        UUID(as_uuid=True),
        ForeignKey(FK_CHAT_ROOMS_ID, ondelete="CASCADE"),
        nullable=False,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey(FK_USERS_ID, ondelete="CASCADE"),
        nullable=False,
    )
    role = Column(ChatRoomMemberRoleEnum, nullable=False, default="MEMBER")
    last_read_at = Column(DateTime(timezone=True), nullable=True)
    joined_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(dt.timezone.utc),
        nullable=False,
    )
    left_at = Column(DateTime(timezone=True), nullable=True)

    room = relationship("ChatRoom", back_populates="members")
    user = relationship("Users")

    __table_args__ = (
        UniqueConstraint("room_id", "user_id", name="uq_chat_room_members_room_user"),
        Index("idx_chat_room_members_room_id", "room_id"),
        Index("idx_chat_room_members_user_id", "user_id"),
    )


class ChatMessageReaction(Base):
    __tablename__ = "chat_message_reactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    message_id = Column(
        UUID(as_uuid=True),
        ForeignKey(FK_CHAT_MESSAGES_ID, ondelete="CASCADE"),
        nullable=False,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey(FK_USERS_ID, ondelete="CASCADE"),
        nullable=False,
    )
    emoji = Column(String(16), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(dt.timezone.utc),
        nullable=False,
    )

    message = relationship("ChatMessage", back_populates="reactions")
    user = relationship("Users")

    __table_args__ = (
        UniqueConstraint(
            "message_id",
            "user_id",
            "emoji",
            name="uq_chat_message_reactions_message_user_emoji",
        ),
        Index("idx_chat_message_reactions_message_id", "message_id"),
    )


class ChatMessageReport(Base):
    __tablename__ = "chat_message_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    message_id = Column(
        UUID(as_uuid=True),
        ForeignKey(FK_CHAT_MESSAGES_ID, ondelete="CASCADE"),
        nullable=False,
    )
    reporter_id = Column(
        UUID(as_uuid=True),
        ForeignKey(FK_USERS_ID, ondelete="CASCADE"),
        nullable=False,
    )
    reason = Column(String(32), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(dt.timezone.utc),
        nullable=False,
    )
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    message = relationship("ChatMessage")
    reporter = relationship("Users")

    __table_args__ = (
        UniqueConstraint(
            "message_id",
            "reporter_id",
            name="uq_chat_message_reports_message_reporter",
        ),
        Index("idx_chat_message_reports_message_id", "message_id"),
        Index(
            "idx_chat_message_reports_unresolved",
            "created_at",
            postgresql_where=sql_text("resolved_at IS NULL"),
        ),
    )
