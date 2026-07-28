import asyncio
import json
import logging
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, WebSocket
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette import status
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK

from pecha_api.group_posts.comment_response_models import (
    CreateGroupPostCommentRequest,
    GroupPostCommentDTO,
    GroupPostCommentsResponse,
)
from pecha_api.group_posts.comment_service import (
    create_post_comment_service,
    delete_post_comment_service,
    list_post_comments_service,
)
from pecha_api.group_posts.comment_websocket import get_broadcaster
from pecha_api.plans.authors.plan_authors_service import validate_and_extract_author_details

logger = logging.getLogger(__name__)

oauth2_scheme = HTTPBearer()

public_group_post_comments_router = APIRouter(
    prefix="/author/groups/{group_id}/posts/{post_id}/comments",
    tags=["Public Group Post Comments"],
)


@public_group_post_comments_router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=GroupPostCommentsResponse,
)
def list_post_comments(
    group_id: UUID,
    post_id: UUID,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """List comments on a post (newest first)."""
    return list_post_comments_service(
        group_id=group_id,
        post_id=post_id,
        skip=skip,
        limit=limit,
    )


@public_group_post_comments_router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=GroupPostCommentDTO,
)
def create_post_comment(
    group_id: UUID,
    post_id: UUID,
    request: CreateGroupPostCommentRequest,
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
):
    """Create a comment on a post (requires authentication)."""
    author = validate_and_extract_author_details(token=authentication_credential.credentials)
    return create_post_comment_service(
        group_id=group_id,
        post_id=post_id,
        author_email=author.email,
        text=request.text,
    )


@public_group_post_comments_router.delete(
    "/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_post_comment(
    group_id: UUID,
    post_id: UUID,
    comment_id: UUID,
    authentication_credential: Annotated[HTTPAuthorizationCredentials, Depends(oauth2_scheme)],
):
    """Delete a comment (only the author can delete)."""
    author = validate_and_extract_author_details(token=authentication_credential.credentials)
    delete_post_comment_service(
        group_id=group_id,
        post_id=post_id,
        comment_id=comment_id,
        user_id=author.id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@public_group_post_comments_router.websocket(
    "/live"
)
async def websocket_post_comments(
    websocket: WebSocket,
    group_id: UUID,
    post_id: UUID,
    token: str = Query(...),
):
    """Live comment stream for a post (WebSocket)."""
    author = None

    try:
        broadcaster = get_broadcaster()
    except RuntimeError as e:
        logger.error(f"Broadcaster not initialized: {e}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="Redis unavailable")
        return

    try:
        # 1. Authenticate
        try:
            author = validate_and_extract_author_details(token=token)
        except HTTPException as auth_error:
            logger.error(f"WebSocket auth failed: {auth_error.detail}")
            await websocket.accept()
            await websocket.send_json({
                "type": "error",
                "code": "UNAUTHORIZED",
                "message": str(auth_error.detail)
            })
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Unauthorized")
            return

        # 2. Validate group & post exist (synchronous)
        from pecha_api.db.database import SessionLocal
        from pecha_api.group_posts.comment_service import (
            _validate_group_is_public,
            _validate_post_published,
        )

        with SessionLocal() as db:
            _validate_group_is_public(db, group_id)
            _validate_post_published(db, post_id, group_id)

        # 3. Accept, track connection, and subscribe to Redis channel
        await websocket.accept()
        await broadcaster.add_connection(post_id, author.id, websocket)
        pubsub = await broadcaster.subscribe_to_post(post_id)

        # 4a. Background task: listen for Redis pub/sub messages
        async def listen_redis():
            try:
                async for message in pubsub.listen():
                    if message["type"] == "message":
                        try:
                            await websocket.send_text(message["data"])
                        except (ConnectionClosedOK, ConnectionClosedError):
                            break
            except Exception as e:
                logger.error(f"Error listening to Redis: {e}")

        redis_task = asyncio.create_task(listen_redis())

        # 4b. Main task: listen for client messages
        try:
            while True:
                data = await websocket.receive_json()

                if data.get("type") != "comment":
                    await websocket.send_json({
                        "type": "error",
                        "code": "INVALID_MESSAGE",
                        "message": "Only 'comment' type messages are supported"
                    })
                    continue

                # 5. Create comment via existing service
                try:
                    comment_dto = create_post_comment_service(
                        group_id=group_id,
                        post_id=post_id,
                        author_email=author.email,
                        text=data.get("text", ""),
                    )
                except HTTPException as e:
                    logger.error(f"Comment creation failed: {e.detail}")
                    await websocket.send_json({
                        "type": "error",
                        "code": e.detail if isinstance(e.detail, str) else "ERROR",
                        "message": e.detail if isinstance(e.detail, str) else str(e.detail)
                    })
                    continue

                # 6. Broadcast to all servers via Redis pub/sub
                try:
                    await broadcaster.broadcast_comment(post_id, comment_dto)
                except Exception as e:
                    logger.error(f"Failed to broadcast comment {comment_dto.id} to Redis: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "code": "BROADCAST_ERROR",
                        "message": f"Failed to broadcast comment: {str(e)}"
                    })

        finally:
            redis_task.cancel()
            try:
                await pubsub.unsubscribe(f"post:{post_id}:comments")
            except Exception as e:
                logger.error(f"Error unsubscribing from Redis: {e}")

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        except Exception:
            pass

    finally:
        if author:
            await broadcaster.remove_connection(post_id, author.id)
