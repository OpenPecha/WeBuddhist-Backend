import json
import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4
from datetime import datetime, timezone as tz

from pecha_api.chat.response_models import ChatMessageDTO


def _message_dto(room_id) -> ChatMessageDTO:
    return ChatMessageDTO(
        id=uuid4(),
        room_id=room_id,
        sender_id=uuid4(),
        sender_email="sender@example.com",
        body="Hello",
        created_at=datetime.now(tz.utc).isoformat(),
    )


class TestChatBroadcasterUnit:

    @pytest.mark.asyncio
    async def test_broadcaster_initialization(self):
        from pecha_api.chat.chat_websocket import ChatBroadcaster

        redis_url = "redis://localhost:6379/0"
        broadcaster = ChatBroadcaster(redis_url)

        assert broadcaster.redis_url == redis_url
        assert broadcaster.redis is None
        assert broadcaster.connections == {}

    @pytest.mark.asyncio
    async def test_broadcaster_connect_disconnect(self):
        from pecha_api.chat.chat_websocket import ChatBroadcaster

        broadcaster = ChatBroadcaster("redis://localhost:6379/0")
        mock_redis = AsyncMock()

        async def mock_from_url(*args, **kwargs):
            return mock_redis

        with patch("pecha_api.chat.chat_websocket.Redis.from_url", side_effect=mock_from_url):
            await broadcaster.connect()
            assert broadcaster.redis is not None

            await broadcaster.disconnect()
            mock_redis.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_broadcaster_add_remove_connection(self):
        from pecha_api.chat.chat_websocket import ChatBroadcaster

        broadcaster = ChatBroadcaster("redis://localhost:6379/0")
        broadcaster.redis = AsyncMock()

        room_id = uuid4()
        user_id = uuid4()
        mock_ws = AsyncMock()

        await broadcaster.add_connection(room_id, user_id, mock_ws)
        assert room_id in broadcaster.connections
        assert user_id in broadcaster.connections[room_id]
        broadcaster.redis.sadd.assert_called_once()

        await broadcaster.remove_connection(room_id, user_id)
        assert room_id not in broadcaster.connections
        broadcaster.redis.srem.assert_called_once()

    @pytest.mark.asyncio
    async def test_broadcaster_broadcast_message(self):
        from pecha_api.chat.chat_websocket import ChatBroadcaster

        broadcaster = ChatBroadcaster("redis://localhost:6379/0")
        broadcaster.redis = AsyncMock()

        room_id = uuid4()
        message = _message_dto(room_id)

        await broadcaster.broadcast_message(room_id, message)

        broadcaster.redis.publish.assert_called_once()
        channel, payload = broadcaster.redis.publish.call_args.args
        assert channel == f"chat:room:{room_id}:messages"
        parsed = json.loads(payload)
        assert parsed["type"] == "message_created"
        assert parsed["message"]["body"] == "Hello"

    @pytest.mark.asyncio
    async def test_broadcaster_broadcast_typing(self):
        from pecha_api.chat.chat_websocket import ChatBroadcaster

        broadcaster = ChatBroadcaster("redis://localhost:6379/0")
        broadcaster.redis = AsyncMock()

        room_id = uuid4()
        user_id = uuid4()

        await broadcaster.broadcast_typing(room_id, user_id, "typer@example.com", is_typing=True)

        broadcaster.redis.publish.assert_called_once()
        channel, payload = broadcaster.redis.publish.call_args.args
        assert channel == f"chat:room:{room_id}:messages"
        parsed = json.loads(payload)
        assert parsed["type"] == "typing"
        assert parsed["user_id"] == str(user_id)
        assert parsed["email"] == "typer@example.com"
        assert parsed["is_typing"] is True

    def test_get_broadcaster_raises_when_not_initialized(self):
        import pecha_api.chat.chat_websocket as chat_websocket_module
        from pecha_api.chat.chat_websocket import get_broadcaster

        original = chat_websocket_module.broadcaster
        chat_websocket_module.broadcaster = None
        try:
            with pytest.raises(RuntimeError):
                get_broadcaster()
        finally:
            chat_websocket_module.broadcaster = original
