import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone as tz
from fastapi import HTTPException
from starlette import status

# Import the app first so the full SQLAlchemy model registry is configured
# before any ChatRoom()/ChatRoomMember() instantiation below triggers mapper configuration.
import pecha_api.app  # noqa: F401

from pecha_api.chat.service import (
    build_message_dto,
    resolve_or_create_group_room,
    resolve_or_create_private_room,
)


class MockUser:
    def __init__(self, user_id=None, email="user@example.com", firstname="Alice"):
        self.id = user_id or uuid4()
        self.email = email
        self.firstname = firstname


class MockMessage:
    def __init__(self, sender=None, sender_id=None, room_id=None, body="Hello"):
        self.id = uuid4()
        self.room_id = room_id or uuid4()
        self.sender_id = sender_id or uuid4()
        self.sender = sender or MockUser(user_id=self.sender_id)
        self.body = body
        self.created_at = datetime.now(tz.utc)
        self.deleted_at = None


class MockGroup:
    def __init__(self, id=None, avatar_key=None, metadata_entries=None, slug="my-group"):
        self.id = id or uuid4()
        self.avatar_key = avatar_key
        self.metadata_entries = metadata_entries or []
        self.slug = slug


class TestBuildMessageDTO:
    def test_uses_placeholder_email_when_sender_missing(self):
        message = MockMessage()
        message.sender = None

        dto = build_message_dto(message)

        assert dto.sender_email == "unknown@example.com"


class TestResolveOrCreateGroupRoom:

    @patch('pecha_api.chat.service.add_member')
    @patch('pecha_api.chat.service.create_room')
    @patch('pecha_api.chat.service.is_user_following_group')
    @patch('pecha_api.chat.service.is_user_joined_group')
    @patch('pecha_api.chat.service.get_group_by_id')
    @patch('pecha_api.chat.service.get_room_by_group_id')
    def test_creates_room_and_creator_membership_on_first_message(
        self, mock_get_room, mock_get_group, mock_joined, mock_following,
        mock_create_room, mock_add_member,
    ):
        group_id = uuid4()
        user = MockUser()
        mock_get_room.return_value = None
        mock_get_group.return_value = MockGroup(id=group_id)
        mock_joined.return_value = True
        mock_following.return_value = False

        created_room = MagicMock(id=uuid4(), group_id=group_id)
        mock_create_room.return_value = created_room

        result = resolve_or_create_group_room(db=MagicMock(), group_id=group_id, user=user)

        assert result is created_room
        mock_add_member.assert_called_once()
        member_arg = mock_add_member.call_args.kwargs["member"]
        assert member_arg.role == "CREATOR"
        assert member_arg.user_id == user.id

    @patch('pecha_api.chat.service.get_room_by_group_id')
    def test_reuses_existing_room(self, mock_get_room):
        existing_room = MagicMock()
        mock_get_room.return_value = existing_room

        result = resolve_or_create_group_room(db=MagicMock(), group_id=uuid4(), user=MockUser())

        assert result is existing_room

    @patch('pecha_api.chat.service.is_user_following_group')
    @patch('pecha_api.chat.service.is_user_joined_group')
    @patch('pecha_api.chat.service.get_group_by_id')
    @patch('pecha_api.chat.service.get_room_by_group_id')
    def test_ineligible_user_forbidden(
        self, mock_get_room, mock_get_group, mock_joined, mock_following
    ):
        mock_get_room.return_value = None
        mock_get_group.return_value = MockGroup()
        mock_joined.return_value = False
        mock_following.return_value = False

        with pytest.raises(HTTPException) as exc_info:
            resolve_or_create_group_room(db=MagicMock(), group_id=uuid4(), user=MockUser())

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @patch('pecha_api.chat.service.get_group_by_id')
    @patch('pecha_api.chat.service.get_room_by_group_id')
    def test_group_not_found(self, mock_get_room, mock_get_group):
        mock_get_room.return_value = None
        mock_get_group.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            resolve_or_create_group_room(db=MagicMock(), group_id=uuid4(), user=MockUser())

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


class TestResolveOrCreatePrivateRoom:

    @patch('pecha_api.chat.service.add_member')
    @patch('pecha_api.chat.service.create_room')
    @patch('pecha_api.chat.service.get_room_by_pair')
    def test_creates_normalized_pair_room_on_first_message(
        self, mock_get_pair, mock_create_room, mock_add_member
    ):
        user_a = MockUser(user_id=uuid4())
        user_b_id = uuid4()
        other = MockUser(user_id=user_b_id)
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = other
        mock_get_pair.return_value = None
        created_room = MagicMock(id=uuid4())
        mock_create_room.return_value = created_room

        result = resolve_or_create_private_room(db=mock_db, user=user_a, receiver_id=user_b_id)

        assert result is created_room
        low_id, high_id = sorted([user_a.id, user_b_id])
        mock_get_pair.assert_called_once_with(db=mock_db, low_id=low_id, high_id=high_id)
        assert mock_add_member.call_count == 2

    @patch('pecha_api.chat.service.get_room_by_pair')
    def test_reuses_existing_room_regardless_of_direction(self, mock_get_pair):
        user_a = MockUser(user_id=uuid4())
        user_b_id = uuid4()
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = MockUser(user_id=user_b_id)
        existing_room = MagicMock()
        mock_get_pair.return_value = existing_room

        result = resolve_or_create_private_room(db=mock_db, user=user_a, receiver_id=user_b_id)

        assert result is existing_room

    def test_cannot_dm_self(self):
        user = MockUser()

        with pytest.raises(HTTPException) as exc_info:
            resolve_or_create_private_room(db=MagicMock(), user=user, receiver_id=user.id)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST

    def test_receiver_not_found(self):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            resolve_or_create_private_room(db=mock_db, user=MockUser(), receiver_id=uuid4())

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
