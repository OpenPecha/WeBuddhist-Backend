from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone as tz

from fastapi import HTTPException
from starlette import status

from pecha_api.chat.response_models import (
    ChatMessageDTO,
    ChatMessagesResponse,
    ChatPeopleResponse,
    ChatPersonDTO,
    ChatRoomDTO,
    ChatRoomMembersResponse,
    ChatRoomsResponse,
)


def get_client():
    from pecha_api.app import api
    from fastapi.testclient import TestClient
    return TestClient(api)


AUTH_HEADERS = {"Authorization": "Bearer test-token"}


def _message_dto(room_id=None) -> ChatMessageDTO:
    return ChatMessageDTO(
        id=uuid4(),
        room_id=room_id or uuid4(),
        sender_id=uuid4(),
        sender_email="sender@example.com",
        body="Hello",
        created_at=datetime.now(tz.utc).isoformat(),
    )


def _room_dto(room_id=None) -> ChatRoomDTO:
    return ChatRoomDTO(
        id=room_id or uuid4(),
        group_id=uuid4(),
        kind="GROUP",
        name="My Group Chat",
        img_url=None,
        created_by=uuid4(),
        member_count=1,
        updated_at=datetime.now(tz.utc).isoformat(),
        last_message=None,
        unread_count=0,
    )


class TestListMyRooms:

    @patch('pecha_api.chat.views.list_my_rooms_service')
    @patch('pecha_api.chat.views.validate_and_extract_user_details')
    def test_list_rooms(self, mock_validate, mock_service):
        client = get_client()
        mock_validate.return_value = MagicMock()
        mock_service.return_value = ChatRoomsResponse(rooms=[_room_dto()], skip=0, limit=20, total=1)

        response = client.get("/chat/rooms", headers=AUTH_HEADERS)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["total"] == 1

    def test_requires_auth(self):
        client = get_client()

        response = client.get("/chat/rooms")

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestSendGroupMessage:

    @patch('pecha_api.chat.views.send_group_message_service')
    @patch('pecha_api.chat.views.validate_and_extract_user_details')
    def test_send_message_creates_or_reuses_room(self, mock_validate, mock_service):
        client = get_client()
        group_id = uuid4()
        mock_validate.return_value = MagicMock()
        mock_service.return_value = _message_dto()

        response = client.post(
            f"/chat/groups/{group_id}/messages",
            headers=AUTH_HEADERS,
            json={"body": "Hello group"},
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["body"] == "Hello"

    @patch('pecha_api.chat.views.send_group_message_service')
    @patch('pecha_api.chat.views.validate_and_extract_user_details')
    def test_rejects_blank_body(self, mock_validate, mock_service):
        client = get_client()

        response = client.post(
            f"/chat/groups/{uuid4()}/messages",
            headers=AUTH_HEADERS,
            json={"body": "   "},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        mock_service.assert_not_called()

    @patch('pecha_api.chat.views.send_group_message_service')
    @patch('pecha_api.chat.views.validate_and_extract_user_details')
    def test_propagates_forbidden_from_service(self, mock_validate, mock_service):
        client = get_client()
        mock_validate.return_value = MagicMock()
        mock_service.side_effect = HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

        response = client.post(
            f"/chat/groups/{uuid4()}/messages",
            headers=AUTH_HEADERS,
            json={"body": "Hello"},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestListGroupPeople:

    @patch('pecha_api.chat.views.list_group_people_service')
    @patch('pecha_api.chat.views.validate_and_extract_user_details')
    def test_list_people(self, mock_validate, mock_service):
        client = get_client()
        mock_validate.return_value = MagicMock()
        mock_service.return_value = ChatPeopleResponse(
            people=[ChatPersonDTO(user_id=uuid4(), email="bob@example.com", firstname="Bob", lastname="Smith")],
            skip=0,
            limit=50,
            total=1,
        )

        response = client.get(f"/chat/groups/{uuid4()}/people", headers=AUTH_HEADERS)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["total"] == 1
        assert response.json()["people"][0]["email"] == "bob@example.com"

    def test_requires_auth(self):
        client = get_client()

        response = client.get(f"/chat/groups/{uuid4()}/people")

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestSendDirectMessage:

    @patch('pecha_api.chat.views.send_direct_message_service')
    @patch('pecha_api.chat.views.validate_and_extract_user_details')
    def test_send_dm(self, mock_validate, mock_service):
        client = get_client()
        mock_validate.return_value = MagicMock()
        mock_service.return_value = _message_dto()

        response = client.post(
            f"/chat/users/{uuid4()}/messages",
            headers=AUTH_HEADERS,
            json={"body": "Hey there"},
        )

        assert response.status_code == status.HTTP_201_CREATED


class TestRoomMembers:

    @patch('pecha_api.chat.views.add_room_members_service')
    @patch('pecha_api.chat.views.validate_and_extract_user_details')
    def test_add_members(self, mock_validate, mock_service):
        client = get_client()
        mock_validate.return_value = MagicMock()
        mock_service.return_value = ChatRoomMembersResponse(members=[], skip=0, limit=1000, total=0)

        response = client.post(
            f"/chat/rooms/{uuid4()}/members",
            headers=AUTH_HEADERS,
            json={"user_ids": [str(uuid4())]},
        )

        assert response.status_code == status.HTTP_200_OK

    @patch('pecha_api.chat.views.remove_room_member_service')
    @patch('pecha_api.chat.views.validate_and_extract_user_details')
    def test_remove_member(self, mock_validate, mock_service):
        client = get_client()
        mock_validate.return_value = MagicMock()
        mock_service.return_value = None

        response = client.delete(
            f"/chat/rooms/{uuid4()}/members/{uuid4()}",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT


class TestRoomMessages:

    @patch('pecha_api.chat.views.list_room_messages_service')
    @patch('pecha_api.chat.views.validate_and_extract_user_details')
    def test_list_messages(self, mock_validate, mock_service):
        client = get_client()
        mock_validate.return_value = MagicMock()
        mock_service.return_value = ChatMessagesResponse(messages=[_message_dto()], skip=0, limit=20, total=1)

        response = client.get(f"/chat/rooms/{uuid4()}/messages", headers=AUTH_HEADERS)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["total"] == 1

    @patch('pecha_api.chat.views.delete_message_service')
    @patch('pecha_api.chat.views.validate_and_extract_user_details')
    def test_delete_message(self, mock_validate, mock_service):
        client = get_client()
        mock_validate.return_value = MagicMock()
        mock_service.return_value = None

        response = client.delete(
            f"/chat/rooms/{uuid4()}/messages/{uuid4()}",
            headers=AUTH_HEADERS,
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT


class TestRoomDetailAndProfile:

    @patch('pecha_api.chat.views.get_room_detail_service')
    @patch('pecha_api.chat.views.validate_and_extract_user_details')
    def test_get_room_detail(self, mock_validate, mock_service):
        client = get_client()
        room = _room_dto()
        mock_validate.return_value = MagicMock()
        mock_service.return_value = room

        response = client.get(f"/chat/rooms/{room.id}", headers=AUTH_HEADERS)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["id"] == str(room.id)

    @patch('pecha_api.chat.views.update_room_profile_service')
    @patch('pecha_api.chat.views.validate_and_extract_user_details')
    def test_update_room_profile(self, mock_validate, mock_service):
        client = get_client()
        room = _room_dto()
        mock_validate.return_value = MagicMock()
        mock_service.return_value = room

        response = client.patch(
            f"/chat/rooms/{room.id}",
            headers=AUTH_HEADERS,
            json={"name": "Renamed"},
        )

        assert response.status_code == status.HTTP_200_OK
        mock_service.assert_called_once()

    @patch('pecha_api.chat.views.mark_room_read_service')
    @patch('pecha_api.chat.views.validate_and_extract_user_details')
    def test_mark_room_read(self, mock_validate, mock_service):
        client = get_client()
        mock_validate.return_value = MagicMock()
        mock_service.return_value = None

        response = client.post(f"/chat/rooms/{uuid4()}/read", headers=AUTH_HEADERS)

        assert response.status_code == status.HTTP_204_NO_CONTENT

    @patch('pecha_api.chat.views.list_room_members_service')
    @patch('pecha_api.chat.views.validate_and_extract_user_details')
    def test_list_room_members(self, mock_validate, mock_service):
        client = get_client()
        mock_validate.return_value = MagicMock()
        mock_service.return_value = ChatRoomMembersResponse(members=[], skip=0, limit=20, total=0)

        response = client.get(f"/chat/rooms/{uuid4()}/members", headers=AUTH_HEADERS)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["total"] == 0
