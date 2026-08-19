import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone as tz
from fastapi import HTTPException
from starlette import status

# Import the app first so the full SQLAlchemy model registry is configured
# before any ChatRoom()/ChatRoomMember() instantiation below triggers mapper configuration.
import pecha_api.app  # noqa: F401

from pecha_api.chat.member_service import (
    add_room_members_service,
    list_room_members_service,
    remove_room_member_service,
)


class MockUser:
    def __init__(self, user_id=None, email="user@example.com", firstname="Alice", lastname=None):
        self.id = user_id or uuid4()
        self.email = email
        self.firstname = firstname
        self.lastname = lastname


class MockMember:
    def __init__(self, room_id=None, user_id=None, role="MEMBER", left_at=None):
        self.id = uuid4()
        self.room_id = room_id or uuid4()
        self.user_id = user_id or uuid4()
        self.role = role
        self.left_at = left_at
        self.joined_at = datetime.now(tz.utc)
        self.user = MockUser(user_id=self.user_id)


class MockRoom:
    def __init__(self, id=None, group_id=None):
        self.id = id or uuid4()
        self.group_id = group_id or uuid4()
        self.deleted_at = None


class TestListRoomMembersService:

    @patch('pecha_api.chat.member_service.list_active_members')
    @patch('pecha_api.chat.member_service._require_active_member')
    @patch('pecha_api.chat.member_service._get_room_or_404')
    @patch('pecha_api.chat.member_service.SessionLocal')
    def test_lists_members(self, mock_session, mock_get_room, mock_require, mock_list):
        mock_session.return_value.__enter__.return_value = MagicMock()
        member = MockMember()
        mock_list.return_value = ([member], 1)

        result = list_room_members_service(room_id=uuid4(), user=MockUser(), skip=0, limit=20)

        assert result.total == 1
        assert result.members[0].user_id == member.user_id
        assert result.members[0].email == member.user.email


class TestAddRoomMembersService:

    @patch('pecha_api.chat.member_service.list_active_members')
    @patch('pecha_api.chat.member_service.add_member')
    @patch('pecha_api.chat.member_service.get_member')
    @patch('pecha_api.chat.member_service.is_user_following_group')
    @patch('pecha_api.chat.member_service.is_user_joined_group')
    @patch('pecha_api.chat.member_service._require_active_member')
    @patch('pecha_api.chat.member_service._get_room_or_404')
    @patch('pecha_api.chat.member_service.SessionLocal')
    def test_creator_adds_eligible_members(
        self, mock_session, mock_get_room, mock_require_member,
        mock_joined, mock_following, mock_get_member, mock_add_member,
        mock_list_members,
    ):
        mock_session.return_value.__enter__.return_value = MagicMock()
        room = MockRoom()
        mock_get_room.return_value = room
        mock_require_member.return_value = MockMember(role="CREATOR")
        mock_joined.return_value = True
        mock_following.return_value = False
        mock_get_member.return_value = None
        mock_add_member.return_value = MockMember(room_id=room.id)
        mock_list_members.return_value = ([MockMember(room_id=room.id)], 1)

        candidate_id = uuid4()
        result = add_room_members_service(room_id=room.id, user=MockUser(), user_ids=[candidate_id])

        assert result.total == 1
        mock_add_member.assert_called_once()

    @patch('pecha_api.chat.member_service._require_active_member')
    @patch('pecha_api.chat.member_service._get_room_or_404')
    @patch('pecha_api.chat.member_service.SessionLocal')
    def test_rejects_add_members_on_private_room(
        self, mock_session, mock_get_room, mock_require_member
    ):
        mock_session.return_value.__enter__.return_value = MagicMock()
        room = MockRoom()
        room.group_id = None
        mock_get_room.return_value = room

        with pytest.raises(HTTPException) as exc_info:
            add_room_members_service(room_id=room.id, user=MockUser(), user_ids=[uuid4()])

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST

    @patch('pecha_api.chat.member_service._require_active_member')
    @patch('pecha_api.chat.member_service._get_room_or_404')
    @patch('pecha_api.chat.member_service.SessionLocal')
    def test_non_creator_forbidden(self, mock_session, mock_get_room, mock_require_member):
        mock_session.return_value.__enter__.return_value = MagicMock()
        room = MockRoom()
        mock_get_room.return_value = room
        mock_require_member.return_value = MockMember(role="MEMBER")

        with pytest.raises(HTTPException) as exc_info:
            add_room_members_service(room_id=room.id, user=MockUser(), user_ids=[uuid4()])

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @patch('pecha_api.chat.member_service.list_active_members')
    @patch('pecha_api.chat.member_service.add_member')
    @patch('pecha_api.chat.member_service.get_member')
    @patch('pecha_api.chat.member_service.is_user_following_group')
    @patch('pecha_api.chat.member_service.is_user_joined_group')
    @patch('pecha_api.chat.member_service._require_active_member')
    @patch('pecha_api.chat.member_service._get_room_or_404')
    @patch('pecha_api.chat.member_service.SessionLocal')
    def test_ineligible_candidate_is_skipped(
        self, mock_session, mock_get_room, mock_require_member,
        mock_joined, mock_following, mock_get_member, mock_add_member,
        mock_list_members,
    ):
        mock_session.return_value.__enter__.return_value = MagicMock()
        room = MockRoom()
        mock_get_room.return_value = room
        mock_require_member.return_value = MockMember(role="CREATOR")
        mock_joined.return_value = False
        mock_following.return_value = False
        mock_list_members.return_value = ([], 0)

        add_room_members_service(room_id=room.id, user=MockUser(), user_ids=[uuid4()])

        mock_add_member.assert_not_called()

    @patch('pecha_api.chat.member_service.list_active_members')
    @patch('pecha_api.chat.member_service.add_member')
    @patch('pecha_api.chat.member_service.get_member')
    @patch('pecha_api.chat.member_service.is_user_following_group')
    @patch('pecha_api.chat.member_service.is_user_joined_group')
    @patch('pecha_api.chat.member_service._require_active_member')
    @patch('pecha_api.chat.member_service._get_room_or_404')
    @patch('pecha_api.chat.member_service.SessionLocal')
    def test_skips_self_and_already_active_member(
        self, mock_session, mock_get_room, mock_require_member,
        mock_joined, mock_following, mock_get_member, mock_add_member,
        mock_list_members,
    ):
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        room = MockRoom()
        mock_get_room.return_value = room
        caller = MockUser()
        mock_require_member.return_value = MockMember(role="CREATOR", user_id=caller.id)
        mock_joined.return_value = True
        mock_following.return_value = False
        existing = MockMember(left_at=None)
        mock_get_member.return_value = existing
        mock_list_members.return_value = ([], 0)

        add_room_members_service(
            room_id=room.id,
            user=caller,
            user_ids=[caller.id, uuid4()],
        )

        mock_add_member.assert_not_called()

    @patch('pecha_api.chat.member_service.list_active_members')
    @patch('pecha_api.chat.member_service.add_member')
    @patch('pecha_api.chat.member_service.get_member')
    @patch('pecha_api.chat.member_service.is_user_following_group')
    @patch('pecha_api.chat.member_service.is_user_joined_group')
    @patch('pecha_api.chat.member_service._require_active_member')
    @patch('pecha_api.chat.member_service._get_room_or_404')
    @patch('pecha_api.chat.member_service.SessionLocal')
    def test_rejoins_previously_left_member(
        self, mock_session, mock_get_room, mock_require_member,
        mock_joined, mock_following, mock_get_member, mock_add_member,
        mock_list_members,
    ):
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        room = MockRoom()
        mock_get_room.return_value = room
        mock_require_member.return_value = MockMember(role="CREATOR")
        mock_joined.return_value = True
        mock_following.return_value = False
        existing = MockMember(left_at=datetime.now(tz.utc))
        mock_get_member.return_value = existing
        mock_list_members.return_value = ([existing], 1)

        add_room_members_service(room_id=room.id, user=MockUser(), user_ids=[uuid4()])

        assert existing.left_at is None
        mock_db.commit.assert_called()
        mock_add_member.assert_not_called()


class TestRemoveRoomMemberService:

    @patch('pecha_api.chat.member_service.count_active_members')
    @patch('pecha_api.chat.member_service.get_active_member')
    @patch('pecha_api.chat.member_service._require_active_member')
    @patch('pecha_api.chat.member_service._get_room_or_404')
    @patch('pecha_api.chat.member_service.SessionLocal')
    def test_member_can_leave_self(
        self, mock_session, mock_get_room, mock_require_member,
        mock_get_active, mock_count,
    ):
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        room = MockRoom()
        mock_get_room.return_value = room
        user_id = uuid4()
        mock_require_member.return_value = MockMember(role="MEMBER", user_id=user_id)
        mock_get_active.return_value = MockMember(role="MEMBER", user_id=user_id)

        remove_room_member_service(room_id=room.id, user=MockUser(user_id=user_id), target_user_id=user_id)

        mock_db.commit.assert_called()

    @patch('pecha_api.chat.member_service.get_active_member')
    @patch('pecha_api.chat.member_service._require_active_member')
    @patch('pecha_api.chat.member_service._get_room_or_404')
    @patch('pecha_api.chat.member_service.SessionLocal')
    def test_non_creator_cannot_remove_others(
        self, mock_session, mock_get_room, mock_require_member, mock_get_active
    ):
        mock_session.return_value.__enter__.return_value = MagicMock()
        room = MockRoom()
        mock_get_room.return_value = room
        mock_require_member.return_value = MockMember(role="MEMBER")
        mock_get_active.return_value = MockMember(role="MEMBER")

        with pytest.raises(HTTPException) as exc_info:
            remove_room_member_service(room_id=room.id, user=MockUser(), target_user_id=uuid4())

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN

    @patch('pecha_api.chat.member_service.count_active_members')
    @patch('pecha_api.chat.member_service.get_active_member')
    @patch('pecha_api.chat.member_service._require_active_member')
    @patch('pecha_api.chat.member_service._get_room_or_404')
    @patch('pecha_api.chat.member_service.SessionLocal')
    def test_creator_cannot_leave_while_others_remain(
        self, mock_session, mock_get_room, mock_require_member,
        mock_get_active, mock_count,
    ):
        mock_session.return_value.__enter__.return_value = MagicMock()
        room = MockRoom()
        mock_get_room.return_value = room
        user_id = uuid4()
        creator_member = MockMember(role="CREATOR", user_id=user_id)
        mock_require_member.return_value = creator_member
        mock_get_active.return_value = creator_member
        mock_count.return_value = 2  # creator + 1 other still active

        with pytest.raises(HTTPException) as exc_info:
            remove_room_member_service(room_id=room.id, user=MockUser(user_id=user_id), target_user_id=user_id)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST

    @patch('pecha_api.chat.member_service.get_active_member')
    @patch('pecha_api.chat.member_service._require_active_member')
    @patch('pecha_api.chat.member_service._get_room_or_404')
    @patch('pecha_api.chat.member_service.SessionLocal')
    def test_target_not_found(self, mock_session, mock_get_room, mock_require_member, mock_get_active):
        mock_session.return_value.__enter__.return_value = MagicMock()
        mock_get_room.return_value = MockRoom()
        mock_require_member.return_value = MockMember(role="CREATOR")
        mock_get_active.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            remove_room_member_service(room_id=uuid4(), user=MockUser(), target_user_id=uuid4())

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
