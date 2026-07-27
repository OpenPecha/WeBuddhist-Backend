import pytest
from unittest.mock import patch, AsyncMock, MagicMock, ANY
from uuid import uuid4
from datetime import datetime, timezone as tz

from pecha_api.group_posts.comment_response_models import GroupPostCommentDTO


class MockUser:
    def __init__(self, user_id=None, email="user@example.com"):
        self.id = user_id or uuid4()
        self.email = email


class TestPostCommentBroadcasterUnit:
    """Unit tests for PostCommentBroadcaster class."""

    @pytest.mark.asyncio
    async def test_broadcaster_initialization(self):
        """Test broadcaster initializes correctly."""
        from pecha_api.group_posts.comment_websocket import PostCommentBroadcaster

        redis_url = "redis://localhost:6379/0"
        broadcaster = PostCommentBroadcaster(redis_url)

        assert broadcaster.redis_url == redis_url
        assert broadcaster.redis is None
        assert broadcaster.connections == {}

    @pytest.mark.asyncio
    async def test_broadcaster_connect_disconnect(self):
        """Test broadcaster connection lifecycle."""
        from pecha_api.group_posts.comment_websocket import PostCommentBroadcaster
        from unittest.mock import AsyncMock, patch

        redis_url = "redis://localhost:6379/0"
        broadcaster = PostCommentBroadcaster(redis_url)

        # Mock Redis connection with an async function that returns mock
        mock_redis = AsyncMock()

        async def mock_from_url(*args, **kwargs):
            return mock_redis

        with patch("pecha_api.group_posts.comment_websocket.Redis.from_url", side_effect=mock_from_url):
            await broadcaster.connect()
            assert broadcaster.redis is not None

            await broadcaster.disconnect()
            mock_redis.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_broadcaster_add_remove_connection(self):
        """Test tracking WebSocket connections."""
        from pecha_api.group_posts.comment_websocket import PostCommentBroadcaster
        from unittest.mock import AsyncMock, patch

        broadcaster = PostCommentBroadcaster("redis://localhost:6379/0")
        broadcaster.redis = AsyncMock()

        post_id = uuid4()
        user_id = uuid4()
        mock_ws = AsyncMock()

        # Add connection
        await broadcaster.add_connection(post_id, user_id, mock_ws)
        assert post_id in broadcaster.connections
        assert user_id in broadcaster.connections[post_id]
        broadcaster.redis.sadd.assert_called_once()

        # Remove connection
        await broadcaster.remove_connection(post_id, user_id)
        assert post_id not in broadcaster.connections
        broadcaster.redis.srem.assert_called_once()

    @pytest.mark.asyncio
    async def test_broadcaster_broadcast_comment(self):
        """Test broadcasting comment to Redis pub/sub."""
        from pecha_api.group_posts.comment_websocket import PostCommentBroadcaster

        broadcaster = PostCommentBroadcaster("redis://localhost:6379/0")
        broadcaster.redis = AsyncMock()

        post_id = uuid4()
        user_id = uuid4()
        now = datetime.now(tz.utc).isoformat()

        comment_dto = GroupPostCommentDTO(
            id=uuid4(),
            post_id=post_id,
            user_id=user_id,
            user_email="test@example.com",
            text="Great post!",
            created_at=now,
            updated_at=now,
        )

        await broadcaster.broadcast_comment(post_id, comment_dto)
        broadcaster.redis.publish.assert_called_once()

        # Verify channel name and message structure
        call_args = broadcaster.redis.publish.call_args
        assert f"post:{post_id}:comments" in str(call_args)

    @pytest.mark.asyncio
    async def test_broadcaster_get_connected_users(self):
        """Test getting connected users from Redis."""
        from pecha_api.group_posts.comment_websocket import PostCommentBroadcaster

        broadcaster = PostCommentBroadcaster("redis://localhost:6379/0")
        broadcaster.redis = AsyncMock()

        post_id = uuid4()
        users = {"user1", "user2", "user3"}
        broadcaster.redis.smembers.return_value = users

        result = await broadcaster.get_connected_users(post_id)
        assert result == users
        broadcaster.redis.smembers.assert_called_once_with(f"post:{post_id}:users")
