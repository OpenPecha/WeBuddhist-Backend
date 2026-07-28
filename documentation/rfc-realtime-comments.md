# RFC: Real-Time Comments on Group Posts

## 1. Summary

Enable live comment updates on group posts via WebSocket. When a user submits a comment, all connected clients viewing that post receive the update instantly.

---

## 2. Motivation

| Today | Gap |
|-------|-----|
| Comments are posted via REST | Users must refresh to see new comments |
| List endpoint paginated | No live notification or real-time sync |
| No presence awareness | Users don't know who else is viewing |

Product need: Social engagement requires instant feedback. Users expect comment feeds to update in real-time (like Instagram, Reddit, YouTube).

---

## 3. Goals

- Instant comment delivery to all clients viewing a post
- Maintain comment order and consistency
- Scale to multiple concurrent users per post
- Degrade gracefully if WebSocket unavailable (fallback to REST polling)
- Reuse existing comment models and permissions

## 4. Non-goals (v1)

- Typing indicators ("User X is typing...")
- Comment edit/delete notifications
- Presence tracking (who's viewing)
- Comment reactions (likes, emoji)
- Message history before connection (clients start fresh on connect)
- Multi-shard/cluster distribution (single-instance first)

---

## 5. Architecture

### 5.1 Connection lifecycle

```
Client connects → WS /author/groups/{group_id}/posts/{post_id}/comments/live?token=...
  ↓
Server authenticates token, adds client to post channel
  ↓
Client sends/receives JSON messages
  ↓
Client disconnects (explicit or timeout)
  ↓
Server removes client from channel, cleans up
```

### 5.2 Message types

**Client → Server:**

```json
{
  "type": "comment",
  "text": "Great post!"
}
```

**Server → Client (on new comment):**

```json
{
  "type": "comment_created",
  "comment": {
    "id": "uuid",
    "post_id": "uuid",
    "user_id": "uuid",
    "user_email": "user@example.com",
    "text": "Great post!",
    "created_at": "2026-07-27T12:00:00Z"
  }
}
```

**Server → Client (error):**

```json
{
  "type": "error",
  "code": "VALIDATION_ERROR",
  "message": "Comment text must not be empty"
}
```

### 5.3 Redis pub/sub orchestration

```python
# pecha_api/group_posts/comment_websocket.py
import aioredis
from typing import Dict, Set

class PostCommentBroadcaster:
    """Manages WebSocket connections and Redis pub/sub for comments."""
    
    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.redis = None
        self.connections = {}  # {post_id: {user_id: websocket, ...}} - local only
    
    async def connect(self) -> None:
        """Initialize Redis connection."""
        self.redis = await aioredis.from_url(self.redis_url, decode_responses=True)
    
    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()
    
    async def add_connection(self, post_id: UUID, user_id: UUID, ws: WebSocket) -> None:
        """Track local WebSocket connection."""
        if post_id not in self.connections:
            self.connections[post_id] = {}
        self.connections[post_id][user_id] = ws
        
        # Track in Redis: post:{post_id}:users = set of user_ids connected on this server
        await self.redis.sadd(f"post:{post_id}:users", str(user_id))
    
    async def remove_connection(self, post_id: UUID, user_id: UUID) -> None:
        """Remove local WebSocket connection."""
        if post_id in self.connections:
            self.connections[post_id].pop(user_id, None)
            if not self.connections[post_id]:
                del self.connections[post_id]
        
        # Cleanup Redis tracking
        await self.redis.srem(f"post:{post_id}:users", str(user_id))
    
    async def broadcast_comment(
        self,
        post_id: UUID,
        comment: GroupPostCommentDTO,
    ) -> None:
        """Publish comment to all servers via Redis pub/sub."""
        channel = f"post:{post_id}:comments"
        message = {
            "type": "comment_created",
            "comment": comment.model_dump(mode="json"),
        }
        
        # Publish to Redis: all servers subscribe to this channel
        await self.redis.publish(channel, json.dumps(message))
    
    async def subscribe_to_post(self, post_id: UUID) -> aioredis.client.PubSub:
        """Subscribe to comment stream for a post."""
        pubsub = self.redis.pubsub()
        await pubsub.subscribe(f"post:{post_id}:comments")
        return pubsub
    
    async def get_connected_users(self, post_id: UUID) -> Set[str]:
        """Get all users connected to a post (across all servers)."""
        return await self.redis.smembers(f"post:{post_id}:users")

# Singleton instance
broadcaster = PostCommentBroadcaster(redis_url=settings.REDIS_URL)
```

**Redis data structures:**
- `post:{post_id}:comments` — pub/sub channel for live comment stream
- `post:{post_id}:users` — set of user IDs currently connected to post (TTL: auto-cleanup on disconnect)
- `post:{post_id}:comment_count` — optional: atomic counter for total comments (if needed for stats)

### 5.4 WebSocket endpoint

```python
@public_group_post_comments_router.websocket(
    "ws:/author/groups/{group_id}/posts/{post_id}/comments/live"
)
async def websocket_post_comments(
    websocket: WebSocket,
    group_id: UUID,
    post_id: UUID,
    token: str = Query(...),
):
    """Live comment stream for a post (WebSocket)."""
    try:
        # 1. Authenticate
        author = validate_and_extract_author_details(token=token)
        
        # 2. Validate group & post exist
        with SessionLocal() as db:
            _validate_group_is_public(db, group_id)
            _validate_post_published(db, post_id, group_id)
        
        # 3. Accept, track connection, and subscribe to Redis channel
        await websocket.accept()
        await broadcaster.add_connection(post_id, author.id, websocket)
        pubsub = await broadcaster.subscribe_to_post(post_id)
        
        # 4a. Background task: listen for Redis pub/sub messages
        async def listen_redis():
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        await websocket.send_text(message["data"])
                    except (ConnectionClosedOK, ConnectionClosedError):
                        break
        
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
                        user_id=author.id,
                        text=data.get("text", ""),
                    )
                except HTTPException as e:
                    await websocket.send_json({
                        "type": "error",
                        "code": e.detail if isinstance(e.detail, str) else "ERROR",
                        "message": e.detail if isinstance(e.detail, str) else str(e.detail)
                    })
                    continue
                
                # 6. Broadcast to all servers via Redis pub/sub
                await broadcaster.broadcast_comment(post_id, comment_dto)
        
        finally:
            redis_task.cancel()
            await pubsub.unsubscribe(f"post:{post_id}:comments")
    
    except WebSocketException:
        pass  # Client disconnect
    finally:
        await broadcaster.remove_connection(post_id, author.id)
```

### 5.5 REST fallback

Clients without WebSocket support (or if WS fails) continue using REST:
- `GET /author/groups/{group_id}/posts/{post_id}/comments?skip=0&limit=20` — poll every 3-5s
- `POST /author/groups/{group_id}/posts/{post_id}/comments` — create comment

When a comment is created (via REST or WS), the `create_post_comment_service` returns the DTO, which is then broadcast via `broadcaster.broadcast_comment()` to all servers' Redis channels.

---

## 6. Implementation order (COMPLETED)

1. ✅ **Redis/Dragonfly setup** — configured `REDIS_URL` in settings
2. ✅ **WebSocket infrastructure** — `comment_websocket.py` with `PostCommentBroadcaster`
3. ✅ **WebSocket endpoint** — added to `comment_views.py` at `/author/groups/{group_id}/posts/{post_id}/comments/live?token=...`
4. ✅ **Lifecycle hooks** — app startup: `broadcaster.connect()`, app shutdown: `broadcaster.disconnect()` in `mongo_database.py`
5. ✅ **Tests** — 5 unit tests for broadcaster with mocked Redis
6. ⏳ **Client library** (separate PR) — JS/React hook for `useLiveComments(postId)`
7. ⏳ **Integration testing** — end-to-end WebSocket tests with actual connections

---

## 7. Deployment notes

- **Redis/Dragonfly required** — must be configured before app starts
- Works across multiple instances out-of-the-box (pub/sub is Redis' job)
- No persistent message queue (messages live only while clients connected)
- Timeouts: 60s idle disconnect, 10s ping/pong keep-alive
- Redis memory usage: ~1KB per connected user per post
  - 10,000 users: ~10 MB
  - 100,000 users: ~100 MB
- Use Dragonfly (drop-in Redis replacement) for better performance if needed

---

## 8. Example client usage (React)

```javascript
// Hook that connects to live comment stream
function useLiveComments(groupId, postId, token) {
  const [comments, setComments] = useState([])
  const [error, setError] = useState(null)
  
  useEffect(() => {
    const ws = new WebSocket(
      `ws://.../author/groups/${groupId}/posts/${postId}/comments/live?token=${token}`
    )
    
    ws.onopen = () => setError(null)
    ws.onerror = () => setError("Connection failed")
    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data)
      if (msg.type === 'comment_created') {
        setComments(prev => [msg.comment, ...prev])
      } else if (msg.type === 'error') {
        setError(msg.message)
      }
    }
    
    return () => ws.close()
  }, [groupId, postId, token])
  
  const sendComment = (text) => {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'comment', text }))
    }
  }
  
  return { comments, error, sendComment }
}
```

---

## 9. Validation rules

- POST request via WS must pass same validation as REST `POST /...comments`
  - Text length 1–5000 chars
  - User must be authenticated
  - Group must be public
  - Post must be published
- Client may send at most 1 comment/second (rate limit if needed)
- Broadcast happens **after** DB commit (no dirty reads)

---

## 10. Error handling

| Error | Response | Action |
|-------|----------|--------|
| Invalid JSON | `{"type": "error", "code": "PARSE_ERROR"}` | Connection stays open |
| Validation fails | `{"type": "error", "code": "VALIDATION_ERROR", "message": "..."}` | User retries |
| Auth invalid | Close WS 401 | Client reconnects with new token |
| Group/post not found | Close WS 404 | Client redirects to 404 page |
| Server error | Log + send error message | Connection stays open, user retries |

---

## 11. Testing

- **Unit:** `PostCommentChannelManager` add/remove/broadcast
- **Integration:** 
  - Connect, send comment, receive broadcast
  - Multiple clients on same post
  - Client disconnect cleanup
  - Auth validation on connect
- **Load:** 100 concurrent clients on one post
- **Fallback:** REST polling works if WS unavailable

---

## 12. Implementation notes (v1 completed)

### Files created/modified:

1. **pecha_api/group_posts/comment_websocket.py** — New file
   - `PostCommentBroadcaster` class with Redis pub/sub coordination
   - Tracks local WebSocket connections per post
   - Publishes comments to Redis channels for multi-instance support
   - Global `broadcaster` singleton initialized on app startup

2. **pecha_api/group_posts/comment_views.py** — Modified
   - Added `/live` WebSocket endpoint at `ws://.../comments/live?token=...`
   - Handles authentication, connection tracking, and message streaming
   - Listens for incoming comments and broadcasts via Redis

3. **pecha_api/db/mongo_database.py** — Modified
   - Added `init_broadcaster()` call in app lifespan startup
   - Added `broadcaster.disconnect()` in lifespan shutdown
   - Imports `init_broadcaster` from comment_websocket module

4. **pecha_api/config.py** — Modified
   - Added `REDIS_URL="redis://localhost:6379/0"` configuration

5. **tests/group_posts/test_group_post_comments_websocket.py** — New file
   - Unit tests for PostCommentBroadcaster class
   - Tests cover: initialization, connect/disconnect, add/remove connections, broadcast, get users

6. **pyproject.toml** — Unchanged
   - redis ^6.0.0 already includes asyncio support via redis.asyncio module

### Redis data model in use:

- `post:{post_id}:comments` — Pub/sub channel for live comment broadcast
- `post:{post_id}:users` — Set of user IDs currently viewing this post

### How it works:

1. Client connects via WebSocket with auth token → broadcaster.add_connection() tracks locally + adds to Redis set
2. Client sends comment → create_post_comment_service() creates in DB → broadcaster.broadcast_comment() publishes to Redis
3. Background task listens to Redis pub/sub channel and sends to WebSocket
4. Client disconnects → broadcaster.remove_connection() cleans up locally + removes from Redis set

---

## 13. Future extensions (v2+)

- Typing indicators: `{"type": "typing", "user_email": "..."}` broadcast via Redis
- Comment edits: `{"type": "comment_updated", "comment_id": "...", "text": "..."}`
- Comment deletes: `{"type": "comment_deleted", "comment_id": "..."}`
- Read receipts: presence tracking per post (extend `post:{post_id}:users` with timestamps)
- Message history: send past N comments on connect (store in Redis sorted set with ZSET)
- Horizontal scaling: add more FastAPI instances, Redis handles all pub/sub orchestration
