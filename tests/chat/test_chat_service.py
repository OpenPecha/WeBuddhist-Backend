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
    build_room_dto,
    list_group_people_service,
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


class MockRoom:
    def __init__(self, id=None, group_id=None, sender_id=None, receiver_id=None, name="Room", created_by=None):
        self.id = id or uuid4()
        self.group_id = group_id
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.name = name
        self.img_url = None
        self.created_by = created_by or uuid4()
        self.updated_at = datetime.now(tz.utc)


class TestBuildRoomDTO:

    @patch('pecha_api.chat.service.count_unread_messages')
    @patch('pecha_api.chat.service.get_active_member')
    @patch('pecha_api.chat.service.count_active_members')
    @patch('pecha_api.chat.service.get_last_message')
    def test_group_room_has_no_other_user_fields(
        self, mock_last_message, mock_count_active, mock_get_active, mock_unread
    ):
        room = MockRoom(group_id=uuid4())
        mock_last_message.return_value = None
        mock_count_active.return_value = 2
        mock_get_active.return_value = None
        mock_unread.return_value = 0

        dto = build_room_dto(db=MagicMock(), room=room, viewer_id=uuid4())

        assert dto.kind == "GROUP"
        assert dto.other_user_id is None
        assert dto.other_user_email is None

    @patch('pecha_api.chat.service.count_unread_messages')
    @patch('pecha_api.chat.service.get_active_member')
    @patch('pecha_api.chat.service.count_active_members')
    @patch('pecha_api.chat.service.get_last_message')
    def test_private_room_resolves_other_participant(
        self, mock_last_message, mock_count_active, mock_get_active, mock_unread
    ):
        viewer_id = uuid4()
        other_id = uuid4()
        room = MockRoom(sender_id=viewer_id, receiver_id=other_id)
        mock_last_message.return_value = None
        mock_count_active.return_value = 2
        mock_get_active.return_value = None
        mock_unread.return_value = 0

        other_user = MockUser(user_id=other_id, email="other@example.com", firstname="Bob")
        other_user.lastname = "Smith"
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = other_user

        dto = build_room_dto(db=mock_db, room=room, viewer_id=viewer_id)

        assert dto.kind == "PRIVATE"
        assert dto.other_user_id == other_id
        assert dto.other_user_email == "other@example.com"
        assert dto.other_user_name == "Bob Smith"


class TestListGroupPeopleService:

    @patch('pecha_api.chat.service.list_group_joiners_paginated')
    @patch('pecha_api.chat.service.get_group_by_id')
    @patch('pecha_api.chat.service.SessionLocal')
    def test_excludes_caller_from_results(self, mock_session, mock_get_group, mock_list_joiners):
        mock_session.return_value.__enter__.return_value = MagicMock()
        mock_get_group.return_value = MockGroup()
        caller = MockUser()
        other = MockUser(email="other@example.com", firstname="Bob")
        other.lastname = "Smith"
        other.avatar_url = None
        mock_list_joiners.return_value = ([caller, other], 2)

        result = list_group_people_service(group_id=uuid4(), user=caller, skip=0, limit=50)

        assert result.total == 2
        assert len(result.people) == 1
        assert result.people[0].email == "other@example.com"

    @patch('pecha_api.chat.service.get_group_by_id')
    @patch('pecha_api.chat.service.SessionLocal')
    def test_group_not_found(self, mock_session, mock_get_group):
        mock_session.return_value.__enter__.return_value = MagicMock()
        mock_get_group.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            list_group_people_service(group_id=uuid4(), user=MockUser(), skip=0, limit=50)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND


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
