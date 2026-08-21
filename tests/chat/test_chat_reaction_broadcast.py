import json
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from uuid import uuid4

from starlette import status

# Import the app first so the full SQLAlchemy model registry is configured.
import pecha_api.app  # noqa: F401

from pecha_api.chat.chat_websocket import ChatBroadcaster
from pecha_api.chat.response_models import ChatMessageReactionDTO
from pecha_api.chat.service import _build_reaction_dtos


class MockUser:
    def __init__(self, email="user@example.com"):
        self.id = uuid4()
        self.email = email


class MockReaction:
    def __init__(self, user_id=None, emoji="🙏"):
        self.user_id = user_id or uuid4()
        self.emoji = emoji


class TestBuildReactionDtosUserIds:

    def test_includes_user_ids_per_emoji(self):
        viewer = uuid4()
        other = uuid4()
        reactions = [
            MockReaction(user_id=viewer, emoji="🙏"),
            MockReaction(user_id=other, emoji="🙏"),
            MockReaction(user_id=other, emoji="👍"),
        ]

        dtos = _build_reaction_dtos(reactions, viewer_id=viewer)

        assert dtos[0].emoji == "🙏"
        assert dtos[0].count == 2
        assert dtos[0].user_ids == [viewer, other]
        assert dtos[0].reacted_by_me is True
        assert dtos[1].emoji == "👍"
        assert dtos[1].user_ids == [other]
        assert dtos[1].reacted_by_me is False


class TestBroadcastReactions:

    @pytest.mark.asyncio
    async def test_publishes_reactions_with_neutral_reacted_by_me(self):
        broadcaster = ChatBroadcaster("redis://test")
        broadcaster.redis = MagicMock()
        broadcaster.redis.publish = AsyncMock()
        room_id = uuid4()
        message_id = uuid4()
        user_id = uuid4()
        reactions = [
            ChatMessageReactionDTO(
                emoji="🙏", count=1, reacted_by_me=True, user_ids=[user_id]
            )
        ]

        await broadcaster.broadcast_reactions(
            room_id=room_id, message_id=message_id, reactions=reactions
        )

        channel, raw = broadcaster.redis.publish.call_args.args
        assert channel == f"chat:room:{room_id}:messages"
        payload = json.loads(raw)
        assert payload["type"] == "reactions_updated"
        assert payload["message_id"] == str(message_id)
        assert payload["reactions"] == [
            {
                "emoji": "🙏",
                "count": 1,
                "reacted_by_me": False,
                "user_ids": [str(user_id)],
            }
        ]


class TestReactionEndpointsBroadcast:

    @patch('pecha_api.chat.views.get_broadcaster')
    @patch('pecha_api.chat.views.add_message_reaction_service')
    @patch('pecha_api.chat.views.validate_and_extract_user_details')
    def test_add_reaction_broadcasts(self, mock_validate, mock_service, mock_get_broadcaster):
        from pecha_api.app import api
        from fastapi.testclient import TestClient

        mock_validate.return_value = MockUser()
        reactions = [ChatMessageReactionDTO(emoji="🙏", count=1, reacted_by_me=True)]
        mock_service.return_value = reactions
        broadcaster = MagicMock()
        broadcaster.broadcast_reactions = AsyncMock()
        mock_get_broadcaster.return_value = broadcaster
        room_id, message_id = uuid4(), uuid4()

        client = TestClient(api)
        response = client.post(
            f"/chat/rooms/{room_id}/messages/{message_id}/reactions",
            json={"emoji": "🙏"},
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == status.HTTP_200_OK
        broadcaster.broadcast_reactions.assert_awaited_once_with(
            room_id=room_id, message_id=message_id, reactions=reactions
        )

    @patch('pecha_api.chat.views.get_broadcaster')
    @patch('pecha_api.chat.views.remove_message_reaction_service')
    @patch('pecha_api.chat.views.validate_and_extract_user_details')
    def test_remove_reaction_broadcasts(self, mock_validate, mock_service, mock_get_broadcaster):
        from pecha_api.app import api
        from fastapi.testclient import TestClient

        mock_validate.return_value = MockUser()
        mock_service.return_value = []
        broadcaster = MagicMock()
        broadcaster.broadcast_reactions = AsyncMock()
        mock_get_broadcaster.return_value = broadcaster
        room_id, message_id = uuid4(), uuid4()

        client = TestClient(api)
        response = client.delete(
            f"/chat/rooms/{room_id}/messages/{message_id}/reactions/%F0%9F%99%8F",
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == status.HTTP_200_OK
        broadcaster.broadcast_reactions.assert_awaited_once_with(
            room_id=room_id, message_id=message_id, reactions=[]
        )

    @patch('pecha_api.chat.views.get_broadcaster')
    @patch('pecha_api.chat.views.add_message_reaction_service')
    @patch('pecha_api.chat.views.validate_and_extract_user_details')
    def test_broadcast_failure_does_not_fail_request(
        self, mock_validate, mock_service, mock_get_broadcaster,
    ):
        from pecha_api.app import api
        from fastapi.testclient import TestClient

        mock_validate.return_value = MockUser()
        mock_service.return_value = [
            ChatMessageReactionDTO(emoji="🙏", count=1, reacted_by_me=True)
        ]
        mock_get_broadcaster.side_effect = RuntimeError("redis down")

        client = TestClient(api)
        response = client.post(
            f"/chat/rooms/{uuid4()}/messages/{uuid4()}/reactions",
            json={"emoji": "🙏"},
            headers={"Authorization": "Bearer test-token"},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()[0]["emoji"] == "🙏"
