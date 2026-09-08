from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, field_validator, model_serializer

from pecha_api.chat.enums import ChatMessageReportReason


class ChatMessageParentDTO(BaseModel):
    """Compact DTO for the message a reply points to (the quoted message)."""
    id: UUID
    sender_id: UUID
    sender_email: str
    sender_name: str
    sender_avatar_url: Optional[str] = None
    body: str
    created_at: str


class ChatMessageReactionUserDTO(BaseModel):
    """Identity of one reactor, for showing who reacted."""
    user_id: UUID
    email: Optional[str] = None
    name: Optional[str] = None


class ChatMessageReactionDTO(BaseModel):
    """Aggregated reactions of one emoji on a message.

    user_ids lets a client receiving a shared broadcast (where reacted_by_me
    cannot be viewer-specific) work out its own reacted state; users carries
    the same people with display identity for who-reacted UI."""
    emoji: str
    count: int
    reacted_by_me: bool = False
    user_ids: List[UUID] = []
    users: List[ChatMessageReactionUserDTO] = []


class ChatMessageDTO(BaseModel):
    """DTO for a single chat message."""
    id: UUID
    room_id: UUID
    sender_id: UUID
    sender_email: str
    sender_name: str
    sender_avatar_url: Optional[str] = None
    body: str
    created_at: str
    deleted_at: Optional[str] = None
    parent: Optional[ChatMessageParentDTO] = None
    reactions: List[ChatMessageReactionDTO] = []

    @model_serializer(mode="wrap")
    def _serialize(self, handler):
        """Omit deleted_at entirely for non-deleted messages instead of sending null."""
        data = handler(self)
        if data.get("deleted_at") is None:
            data.pop("deleted_at", None)
        return data


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
    # PRIVATE rooms only: the other participant (not the caller), so a client
    # can reconnect/DM them again without needing to already know their id.
    other_user_id: Optional[UUID] = None
    other_user_email: Optional[str] = None
    other_user_name: Optional[str] = None


class ChatRoomsResponse(BaseModel):
    """Response for list-my-rooms (inbox) endpoint."""
    rooms: List[ChatRoomDTO]
    skip: int
    limit: int
    total: int


class ChatPersonDTO(BaseModel):
    """DTO for a person the caller could start/continue a DM with."""
    user_id: UUID
    email: str
    firstname: str
    lastname: Optional[str] = None
    avatar_url: Optional[str] = None


class ChatPeopleResponse(BaseModel):
    """Response for the group-people (DM candidates) endpoint."""
    people: List[ChatPersonDTO]
    skip: int
    limit: int
    total: int


class AdminChatReportUserDTO(BaseModel):
    """Identity of a user involved in a moderation report."""
    user_id: UUID
    email: Optional[str] = None
    firstname: Optional[str] = None
    lastname: Optional[str] = None


class AdminChatMessageReportDTO(BaseModel):
    """One moderation report, for the CMS admin reports screen.

    reporter is None for AUTOMATIC (system-generated) reports; message_text
    carries the reported content even when the message itself was never
    stored (profanity rejections) or has been deleted since."""
    id: UUID
    source: str
    reason: str
    description: Optional[str] = None
    message_id: Optional[UUID] = None
    message_text: Optional[str] = None
    room_id: Optional[UUID] = None
    room_name: Optional[str] = None
    reporter: Optional[AdminChatReportUserDTO] = None
    reported_user: Optional[AdminChatReportUserDTO] = None
    created_at: str
    resolved_at: Optional[str] = None


class AdminChatMessageReportsResponse(BaseModel):
    """Response for the CMS admin list-reports endpoint."""
    reports: List[AdminChatMessageReportDTO]
    skip: int
    limit: int
    total: int


class SendChatMessageRequest(BaseModel):
    """Request to send a message to a room (group or DM). Pass
    parent_message_id to send it as a reply to that message."""
    body: str
    parent_message_id: Optional[UUID] = None

    @field_validator("body")
    @classmethod
    def validate_body(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Message body must not be empty")
        if len(value) > 4000:
            raise ValueError("Message body must not exceed 4000 characters")
        return value


class AddChatMessageReactionRequest(BaseModel):
    """Request to add an emoji reaction to a message."""
    emoji: str

    @field_validator("emoji")
    @classmethod
    def validate_emoji(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("emoji must not be empty")
        if len(value) > 16:
            raise ValueError("emoji must not exceed 16 characters")
        return value


class ReportChatMessageRequest(BaseModel):
    """Request to report a message for moderation."""
    reason: ChatMessageReportReason
    description: Optional[str] = None

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        value = value.strip()
        if not value:
            return None
        if len(value) > 1000:
            raise ValueError("description must not exceed 1000 characters")
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
