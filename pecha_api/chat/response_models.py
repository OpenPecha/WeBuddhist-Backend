from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, field_validator


class ChatMessageDTO(BaseModel):
    """DTO for a single chat message."""
    id: UUID
    room_id: UUID
    sender_id: UUID
    sender_email: str
    body: str
    created_at: str


class ChatMessagesResponse(BaseModel):
    """Response for list messages endpoint."""
    messages: List[ChatMessageDTO]
    skip: int
    limit: int
    total: int


class ChatRoomMemberDTO(BaseModel):
    """DTO for a chat room member."""
    user_id: UUID
    email: str
    firstname: str
    lastname: Optional[str] = None
    role: str
    joined_at: str


class ChatRoomMembersResponse(BaseModel):
    """Response for list members endpoint."""
    members: List[ChatRoomMemberDTO]
    skip: int
    limit: int
    total: int


class ChatRoomDTO(BaseModel):
    """DTO for a room, presigned picture, and inbox summary fields."""
    id: UUID
    group_id: Optional[UUID] = None
    sender_id: Optional[UUID] = None
    receiver_id: Optional[UUID] = None
    kind: str
    name: str
    img_url: Optional[str] = None
    created_by: UUID
    member_count: int
    updated_at: str
    last_message: Optional[ChatMessageDTO] = None
    unread_count: int = 0


class ChatRoomsResponse(BaseModel):
    """Response for list-my-rooms (inbox) endpoint."""
    rooms: List[ChatRoomDTO]
    skip: int
    limit: int
    total: int


class SendChatMessageRequest(BaseModel):
    """Request to send a message to a room (group or DM)."""
    body: str

    @field_validator("body")
    @classmethod
    def validate_body(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Message body must not be empty")
        if len(value) > 4000:
            raise ValueError("Message body must not exceed 4000 characters")
        return value


class UpdateChatRoomRequest(BaseModel):
    """Request to update room name / picture."""
    name: Optional[str] = None
    img_url: Optional[str] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("name must not be empty")
        if len(value) > 255:
            raise ValueError("name must not exceed 255 characters")
        return value


class AddChatRoomMembersRequest(BaseModel):
    """Request to add members to a group chat room."""
    user_ids: List[UUID]

    @field_validator("user_ids")
    @classmethod
    def validate_user_ids(cls, value: List[UUID]) -> List[UUID]:
        if not value:
            raise ValueError("user_ids must not be empty")
        return value
