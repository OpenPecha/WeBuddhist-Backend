import json
from contextlib import ExitStack, contextmanager
from datetime import datetime, timezone as tz
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from starlette import status
from starlette.websockets import WebSocketDisconnect

from pecha_api.app import api
from pecha_api.group_posts.comment_response_models import GroupPostCommentDTO

client = TestClient(api)


class MockAuthor:
    def __init__(self, email="user@example.com"):
        self.id = uuid4()
        self.email = email


class FakePubSub:
    """Stands in for a redis.asyncio pubsub object.

    ``listen()`` must be a plain call returning an async iterator, which an
    AsyncMock cannot express.
    """

    def __init__(self, messages=None, listen_error=None, unsubscribe_error=None, keep_alive=False):
        self.messages = messages or []
        self.listen_error = listen_error
        self.unsubscribe_error = unsubscribe_error
        self.unsubscribed = []
        self.keep_alive = keep_alive

    def listen(self):
        return self._listen()

    async def _listen(self):
        if self.listen_error is not None:
            raise self.listen_error
        for message in self.messages:
            yield message
        # If keep_alive is True, wait indefinitely to keep the connection open
        if self.keep_alive:
            import asyncio
            await asyncio.Event().wait()

    async def unsubscribe(self, channel):
        self.unsubscribed.append(channel)
        if self.unsubscribe_error is not None:
            raise self.unsubscribe_error


def _comment_dto(post_id, parent_comment_id=None) -> GroupPostCommentDTO:
    now = datetime.now(tz.utc).isoformat()
    return GroupPostCommentDTO(
        id=uuid4(),
        post_id=post_id,
        user_id=uuid4(),
        parent_comment_id=parent_comment_id,
        user_email="user@example.com",
        text="Great post!",
        created_at=now,
        updated_at=now,
    )


def _ws_url(group_id, post_id, token="test-token"):
    return f"/author/groups/{group_id}/posts/{post_id}/comments/live?token={token}"


@contextmanager
def _websocket_env(
    author=None,
    auth_error=None,
    broadcaster=None,
    pubsub=None,
    validation_error=None,
):
    """Patch every collaborator the websocket endpoint reaches for."""
    if broadcaster is None:
        broadcaster = AsyncMock()
    
    # subscribe_to_post is awaited, so it needs to return an awaitable
    async def mock_subscribe(post_id):
        return pubsub if pubsub is not None else FakePubSub(keep_alive=True)
    broadcaster.subscribe_to_post = mock_subscribe

    with ExitStack() as stack:
        mock_validate = stack.enter_context(
            patch("pecha_api.group_posts.comment_views.validate_and_extract_author_details")
        )
        if auth_error is not None:
            mock_validate.side_effect = auth_error
        else:
            mock_validate.return_value = author or MockAuthor()

        stack.enter_context(
            patch("pecha_api.group_posts.comment_views.get_broadcaster", return_value=broadcaster)
        )
        
        # Mock SessionLocal as a context manager
        mock_session = stack.enter_context(patch("pecha_api.db.database.SessionLocal"))
        mock_db = MagicMock()
        mock_session.return_value.__enter__.return_value = mock_db
        
        # Mock the internal validation functions - patch where they are imported FROM
        mock_get_and_validate = stack.enter_context(
            patch("pecha_api.group_posts.comment_service._get_and_validate_post")
        )
        if validation_error is not None:
            mock_get_and_validate.side_effect = validation_error
        else:
            # Return a mock post and group_id
            mock_post = type('MockPost', (), {'id': uuid4(), 'group_id': uuid4()})
            mock_get_and_validate.return_value = (mock_post, mock_post.group_id)
        
        mock_group_check = stack.enter_context(
            patch("pecha_api.group_posts.comment_service._validate_group_is_public")
        )
        if validation_error is not None:
            mock_group_check.side_effect = validation_error
        
        mock_create = stack.enter_context(
            patch("pecha_api.group_posts.comment_views.create_post_comment_service")
        )
        yield broadcaster, mock_create


class TestWebSocketPostCommentsConnection:

    def test_closes_when_broadcaster_is_unavailable(self):
        with patch(
            "pecha_api.group_posts.comment_views.get_broadcaster",
            side_effect=RuntimeError("Redis down"),
        ):
            with pytest.raises(WebSocketDisconnect):
                with client.websocket_connect(_ws_url(uuid4(), uuid4())):
                    pass

    def test_rejects_invalid_token(self):
        auth_error = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )
        with _websocket_env(auth_error=auth_error) as (broadcaster, _):
            with pytest.raises(WebSocketDisconnect):
                with client.websocket_connect(_ws_url(uuid4(), uuid4(), token="bad")) as websocket:
                    message = websocket.receive_json()
                    assert message["type"] == "error"
                    assert message["code"] == "UNAUTHORIZED"
                    assert message["message"] == "Invalid token"
        
        broadcaster.add_connection.assert_not_awaited()

    def test_closes_when_group_validation_fails(self):
        author = MockAuthor()
        not_found = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
        with _websocket_env(author=author, validation_error=not_found) as (broadcaster, _):
            with pytest.raises(WebSocketDisconnect):
                with client.websocket_connect(_ws_url(uuid4(), uuid4())):
                    pass

        # Validation fails before accept(), so connection is never added
        broadcaster.add_connection.assert_not_awaited()
        broadcaster.remove_connection.assert_not_awaited()

    def test_registers_and_unregisters_connection(self):
        group_id = uuid4()
        post_id = uuid4()
        author = MockAuthor()
        pubsub = FakePubSub(keep_alive=True)

        with _websocket_env(author=author, pubsub=pubsub) as (broadcaster, _):
            # Connection will be accepted, then immediately closed when context exits
            # The websocket waits for messages in an infinite loop, so it will disconnect when we exit
            with pytest.raises(WebSocketDisconnect):
                with client.websocket_connect(_ws_url(group_id, post_id)) as ws:
                    # Close the connection to trigger cleanup
                    pass

        broadcaster.add_connection.assert_awaited_once()
        assert broadcaster.add_connection.await_args.args[:2] == (post_id, author.id)
        broadcaster.remove_connection.assert_awaited_once_with(post_id, author.id)
        assert pubsub.unsubscribed == [f"post:{post_id}:comments"]

    def test_unsubscribe_failure_is_swallowed(self):
        pubsub = FakePubSub(unsubscribe_error=RuntimeError("redis gone"), keep_alive=True)

        with _websocket_env(pubsub=pubsub):
            with pytest.raises(WebSocketDisconnect):
                with client.websocket_connect(_ws_url(uuid4(), uuid4())) as ws:
                    pass

        assert len(pubsub.unsubscribed) == 1


class TestWebSocketPostCommentsRedisStream:

    def test_forwards_published_comments_to_client(self):
        post_id = uuid4()
        payload = json.dumps({"type": "comment_created", "comment": {"text": "from redis"}})
        pubsub = FakePubSub(
            messages=[
                {"type": "subscribe", "data": 1},
                {"type": "message", "data": payload},
            ],
            keep_alive=True
        )

        with _websocket_env(pubsub=pubsub):
            with client.websocket_connect(_ws_url(uuid4(), post_id)) as websocket:
                received = websocket.receive_text()
                assert received == payload

    def test_redis_listen_failure_does_not_break_connection(self):
        # When listen fails, the background task stops but the main loop should continue
        pubsub = FakePubSub(listen_error=RuntimeError("pubsub exploded"), keep_alive=True)

        with _websocket_env(pubsub=pubsub) as (_, mock_create):
            with client.websocket_connect(_ws_url(uuid4(), uuid4())) as websocket:
                websocket.send_json({"type": "ping"})
                message = websocket.receive_json()
                assert message["code"] == "INVALID_MESSAGE"

        mock_create.assert_not_called()


class TestWebSocketPostCommentsMessages:

    def test_rejects_unsupported_message_type(self):
        with _websocket_env(pubsub=FakePubSub(keep_alive=True)) as (_, mock_create):
            with client.websocket_connect(_ws_url(uuid4(), uuid4())) as websocket:
                websocket.send_json({"type": "reaction", "text": "hi"})
                message = websocket.receive_json()
                assert message["type"] == "error"
                assert message["code"] == "INVALID_MESSAGE"
        
        mock_create.assert_not_called()

    def test_creates_and_broadcasts_comment(self):
        group_id = uuid4()
        post_id = uuid4()
        author = MockAuthor()
        dto = _comment_dto(post_id)

        with _websocket_env(author=author, pubsub=FakePubSub(keep_alive=True)) as (broadcaster, mock_create):
            mock_create.return_value = dto
            with client.websocket_connect(_ws_url(group_id, post_id)) as websocket:
                websocket.send_json({"type": "comment", "text": "Great post!"})
                # Give it a moment to process
                import time
                time.sleep(0.1)

        mock_create.assert_called_once_with(
            post_id=post_id,
            author_email=author.email,
            text="Great post!",
            parent_comment_id=None,
        )
        broadcaster.broadcast_comment.assert_awaited_once_with(post_id, dto)

    def test_creates_and_broadcasts_reply(self):
        group_id = uuid4()
        post_id = uuid4()
        parent_comment_id = uuid4()
        author = MockAuthor()
        dto = _comment_dto(post_id, parent_comment_id=parent_comment_id)

        with _websocket_env(author=author, pubsub=FakePubSub(keep_alive=True)) as (broadcaster, mock_create):
            mock_create.return_value = dto
            with client.websocket_connect(_ws_url(group_id, post_id)) as websocket:
                websocket.send_json({
                    "type": "comment",
                    "text": "Nested reply",
                    "parent_comment_id": str(parent_comment_id),
                })
                # Give it a moment to process
                import time
                time.sleep(0.1)

        mock_create.assert_called_once_with(
            post_id=post_id,
            author_email=author.email,
            text="Nested reply",
            parent_comment_id=parent_comment_id,
        )
        broadcaster.broadcast_comment.assert_awaited_once_with(post_id, dto)

    def test_reports_comment_creation_failure(self):
        with _websocket_env(pubsub=FakePubSub(keep_alive=True)) as (broadcaster, mock_create):
            mock_create.side_effect = HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="POST_NOT_FOUND"
            )
            with client.websocket_connect(_ws_url(uuid4(), uuid4())) as websocket:
                websocket.send_json({"type": "comment", "text": "Great post!"})
                message = websocket.receive_json()
                assert message["type"] == "error"
                assert message["code"] == "POST_NOT_FOUND"
        
        broadcaster.broadcast_comment.assert_not_awaited()

    def test_reports_non_string_creation_failure_detail(self):
        with _websocket_env(pubsub=FakePubSub(keep_alive=True)) as (_, mock_create):
            mock_create.side_effect = HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"field": "text"},
            )
            with client.websocket_connect(_ws_url(uuid4(), uuid4())) as websocket:
                websocket.send_json({"type": "comment", "text": "Great post!"})
                message = websocket.receive_json()
                assert message["code"] == "ERROR"
                assert "text" in message["message"]

    def test_reports_broadcast_failure(self):
        post_id = uuid4()

        with _websocket_env(pubsub=FakePubSub(keep_alive=True)) as (broadcaster, mock_create):
            mock_create.return_value = _comment_dto(post_id)
            broadcaster.broadcast_comment.side_effect = RuntimeError("redis publish failed")
            with client.websocket_connect(_ws_url(uuid4(), post_id)) as websocket:
                websocket.send_json({"type": "comment", "text": "Great post!"})
                message = websocket.receive_json()
                assert message["type"] == "error"
                assert message["code"] == "BROADCAST_ERROR"
                assert "redis publish failed" in message["message"]
