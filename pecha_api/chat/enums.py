import enum

from sqlalchemy import Enum


class ChatRoomMemberRole(enum.Enum):
    CREATOR = "CREATOR"
    MEMBER = "MEMBER"


ChatRoomMemberRoleEnum = Enum(
    ChatRoomMemberRole,
    name="chat_room_member_role",
)
