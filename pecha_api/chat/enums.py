import enum

from sqlalchemy import Enum


class ChatRoomMemberRole(enum.Enum):
    CREATOR = "CREATOR"
    MEMBER = "MEMBER"


ChatRoomMemberRoleEnum = Enum(
    ChatRoomMemberRole,
    name="chat_room_member_role",
)


class ChatMessageReportReason(enum.Enum):
    SPAM = "SPAM"
    HARASSMENT = "HARASSMENT"
    HATE_SPEECH = "HATE_SPEECH"
    INAPPROPRIATE = "INAPPROPRIATE"
    INAPPROPRIATE_LANGUAGE = "INAPPROPRIATE_LANGUAGE"
    OTHER = "OTHER"


class ChatMessageReportSource(enum.Enum):
    MANUAL = "MANUAL"
    AUTOMATIC = "AUTOMATIC"
