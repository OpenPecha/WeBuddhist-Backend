import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone as tz
from fastapi import HTTPException
from starlette import status

# Import the app first so the full SQLAlchemy model registry is configured
# before any ChatRoom()/ChatRoomMember() instantiation below triggers mapper configuration.
import pecha_api.app  # noqa: F401

from pecha_api.chat.message_service import (
    delete_message_service,
    send_direct_message_service,
    send_group_message_service,
)


class MockUser:
    def __init__(self, user_id=None, email="user@example.com", firstname="Alice"):
        self.id = user_id or uuid4()
        self.email = email
        self.firstname = firstname


class MockMember:
    def __init__(self, room_id=None, user_id=None, role="MEMBER"):
        self.id = uuid4()
        self.room_id = room_id or uuid4()
        self.user_id = user_id or uuid4()
        self.role = role
        self.left_at = None


class MockMessage:
    def __init__(self, sender=None, sender_id=None, room_id=None, body="Hello"):
        self.id = uuid4()
        self.room_id = room_id or uuid4()
        self.sender_id = sender_id or uuid4()
        self.sender = sender or MockUser(user_id=self.sender_id)
        self.body = body
        self.created_at = datetime.now(tz.utc)
        self.deleted_at = None


class TestSendGroupMessageService:

    @patch('pecha_api.chat.message_service.touch_room')
    @patch('pecha_api.chat.message_service.create_message')
    @patch('pecha_api.chat.message_service._require_active_member')
    @patch('pecha_api.chat.message_service.resolve_or_create_group_room')
    @patch('pecha_api.chat.message_service.SessionLocal')
    def test_sends_message_when_member(
        self, mock_session, mock_resolve, mock_require_member,
        mock_create_message, mock_touch,
    ):
        mock_session.return_value.__enter__.return_value = MagicMock()
        room = MagicMock(id=uuid4())
        mock_resolve.return_value = room
        user = MockUser()
        mock_require_member.return_value = MockMember(room_id=room.id, user_id=user.id)
        mock_create_message.return_value = MockMessage(sender=user, sender_id=user.id, room_id=room.id, body="Hi")

        result = send_group_message_service(group_id=uuid4(), user=user, body="Hi")

        assert result.body == "Hi"
        mock_touch.assert_called_once()

    @patch('pecha_api.chat.message_service._require_active_member')
    @patch('pecha_api.chat.message_service.resolve_or_create_group_room')
    @patch('pecha_api.chat.message_service.SessionLocal')
    def test_non_member_forbidden_on_existing_room(
        self, mock_session, mock_resolve, mock_require_member
    ):
        mock_session.return_value.__enter__.return_value = MagicMock()
        mock_resolve.return_value = MagicMock(id=uuid4())
        mock_require_member.side_effect = HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden"
        )

        with pytest.raises(HTTPException) as exc_info:
            send_group_message_service(group_id=uuid4(), user=MockUser(), body="Hi")

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN


class TestSendDirectMessageService:

    @patch('pecha_api.chat.message_service.touch_room')
    @patch('pecha_api.chat.message_service.create_message')
    @patch('pecha_api.chat.message_service.resolve_or_create_private_room')
    @patch('pecha_api.chat.message_service.SessionLocal')
    def test_sends_dm(self, mock_session, mock_resolve, mock_create_message, mock_touch):
        mock_session.return_value.__enter__.return_value = MagicMock()
        room = MagicMock(id=uuid4())
        mock_resolve.return_value = room
        user = MockUser()
        mock_create_message.return_value = MockMessage(sender=user, sender_id=user.id, room_id=room.id, body="Hey")

        result = send_direct_message_service(receiver_id=uuid4(), user=user, body="Hey")

        assert result.body == "Hey"


class TestDeleteMessageService:

    @patch('pecha_api.chat.message_service.soft_delete_message')
    @patch('pecha_api.chat.message_service.get_message_by_id')
    @patch('pecha_api.chat.message_service._require_active_member')
    @patch('pecha_api.chat.message_service._get_room_or_404')
    @patch('pecha_api.chat.message_service.SessionLocal')
    def test_deletes_own_message(
        self, mock_session, mock_get_room, mock_require_member,
        mock_get_message, mock_soft_delete,
    ):
        mock_session.return_value.__enter__.return_value = MagicMock()
        mock_get_room.return_value = MagicMock()
        mock_require_member.return_value = MockMember()
        user_id = uuid4()
        message = MockMessage(sender_id=user_id)
        mock_get_message.return_value = message

        delete_message_service(room_id=uuid4(), message_id=message.id, user=MockUser(user_id=user_id))

        mock_soft_delete.assert_called_once()

    @patch('pecha_api.chat.message_service.get_message_by_id')
    @patch('pecha_api.chat.message_service._require_active_member')
    @patch('pecha_api.chat.message_service._get_room_or_404')
    @patch('pecha_api.chat.message_service.SessionLocal')
    def test_cannot_delete_others_message(
        self, mock_session, mock_get_room, mock_require_member, mock_get_message
    ):
        mock_session.return_value.__enter__.return_value = MagicMock()
        mock_get_room.return_value = MagicMock()
        mock_require_member.return_value = MockMember()
        message = MockMessage(sender_id=uuid4())
        mock_get_message.return_value = message

        with pytest.raises(HTTPException) as exc_info:
            delete_message_service(room_id=uuid4(), message_id=message.id, user=MockUser())

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @patch('pecha_api.chat.message_service.get_message_by_id')
    @patch('pecha_api.chat.message_service._require_active_member')
    @patch('pecha_api.chat.message_service._get_room_or_404')
    @patch('pecha_api.chat.message_service.SessionLocal')
    def test_message_not_found(
        self, mock_session, mock_get_room, mock_require_member, mock_get_message
    ):
        mock_session.return_value.__enter__.return_value = MagicMock()
        mock_get_room.return_value = MagicMock()
        mock_require_member.return_value = MockMember()
        mock_get_message.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            delete_message_service(room_id=uuid4(), message_id=uuid4(), user=MockUser())

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
