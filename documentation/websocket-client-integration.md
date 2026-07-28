# WebSocket Client Integration Guide

This document explains how to integrate real-time comments on the frontend using the WebSocket endpoint.

## Endpoint

```
ws://localhost:8000/api/v1/author/groups/{group_id}/posts/{post_id}/comments/live?token={auth_token}
```

## Connection Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `group_id` | UUID | Yes | The author group ID |
| `post_id` | UUID | Yes | The post ID within that group |
| `token` | string | Yes | Bearer token for authentication |

## Message Format

### Client → Server (send comment)

```json
{
  "type": "comment",
  "text": "Great post!"
}
```

**Validation:**
- `type` must be `"comment"`
- `text` must be 1–5000 characters
- User must be authenticated (via token)
- Group must be public
- Post must be published

### Server → Client (comment created)

```json
{
  "type": "comment_created",
  "comment": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "post_id": "550e8400-e29b-41d4-a716-446655440001",
    "user_id": "550e8400-e29b-41d4-a716-446655440002",
    "user_email": "user@example.com",
    "text": "Great post!",
    "created_at": "2026-07-27T12:00:00Z",
    "updated_at": "2026-07-27T12:00:00Z"
  }
}
```

### Server → Client (error)

```json
{
  "type": "error",
  "code": "VALIDATION_ERROR",
  "message": "Comment text must not be empty"
}
```

**Error codes:**
- `VALIDATION_ERROR` — Comment failed validation (empty, too long)
- `INVALID_MESSAGE` — Message type not supported
- `SERVER_ERROR` — Unexpected server error

## JavaScript Example

```javascript
function connectToLiveComments(groupId, postId, token) {
  const wsUrl = `ws://localhost:8000/api/v1/author/groups/${groupId}/posts/${postId}/comments/live?token=${token}`;
  
  const ws = new WebSocket(wsUrl);
  
  ws.onopen = () => {
    console.log("Connected to live comments");
  };
  
  ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    
    if (message.type === "comment_created") {
      const comment = message.comment;
      console.log(`New comment from ${comment.user_email}: ${comment.text}`);
      // Update UI with new comment
      addCommentToUI(comment);
    } else if (message.type === "error") {
      console.error(`Error: ${message.code} - ${message.message}`);
    }
  };
  
  ws.onerror = (error) => {
    console.error("WebSocket error:", error);
  };
  
  ws.onclose = () => {
    console.log("Disconnected from live comments");
  };
  
  return {
    send: (text) => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
          type: "comment",
          text: text
        }));
      }
    },
    close: () => {
      ws.close();
    }
  };
}

// Usage
const comments = connectToLiveComments(groupId, postId, authToken);
comments.send("Great post!");
```

## React Hook Example

```javascript
import { useEffect, useRef, useState } from 'react';

function useLiveComments(groupId, postId, token) {
  const [comments, setComments] = useState([]);
  const [error, setError] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef(null);
  
  useEffect(() => {
    if (!groupId || !postId || !token) return;
    
    const wsUrl = `ws://localhost:8000/api/v1/author/groups/${groupId}/posts/${postId}/comments/live?token=${token}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;
    
    ws.onopen = () => {
      setIsConnected(true);
      setError(null);
    };
    
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      
      if (message.type === "comment_created") {
        setComments(prev => [message.comment, ...prev]);
      } else if (message.type === "error") {
        setError(message.message);
      }
    };
    
    ws.onerror = () => {
      setError("WebSocket connection failed");
      setIsConnected(false);
    };
    
    ws.onclose = () => {
      setIsConnected(false);
    };
    
    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, [groupId, postId, token]);
  
  const sendComment = (text) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: "comment",
        text: text
      }));
    }
  };
  
  return {
    comments,
    error,
    isConnected,
    sendComment
  };
}

// Usage in component
export function PostCommentThread({ groupId, postId, token }) {
  const { comments, error, isConnected, sendComment } = useLiveComments(groupId, postId, token);
  const [newComment, setNewComment] = useState("");
  
  const handleSubmit = (e) => {
    e.preventDefault();
    if (newComment.trim()) {
      sendComment(newComment);
      setNewComment("");
    }
  };
  
  return (
    <div>
      <p>{isConnected ? "🟢 Live" : "🔴 Offline"}</p>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      
      <form onSubmit={handleSubmit}>
        <textarea
          value={newComment}
          onChange={(e) => setNewComment(e.target.value)}
          placeholder="Write a comment..."
          maxLength="5000"
        />
        <button type="submit" disabled={!isConnected}>Send</button>
      </form>
      
      <div>
        {comments.map(comment => (
          <div key={comment.id} style={{ borderBottom: "1px solid #ccc", padding: "10px" }}>
            <strong>{comment.user_email}</strong>
            <p>{comment.text}</p>
            <small>{new Date(comment.created_at).toLocaleString()}</small>
          </div>
        ))}
      </div>
    </div>
  );
}
```

## Handling Disconnections

The WebSocket will automatically disconnect if:
- Client closes the connection
- Token expires (60s idle timeout)
- Server crashes or restarts
- Network connection drops

For production, implement:

1. **Automatic reconnection** with exponential backoff
2. **Message queueing** during disconnection
3. **Fallback to REST polling** if WebSocket unavailable
4. **Connection state UI** (online/offline indicator)

## Performance Notes

- **Memory:** ~1KB per connected user per post
- **Latency:** <100ms end-to-end (local network)
- **Throughput:** 100+ concurrent users per post per server
- **Scaling:** Multiple server instances supported via Redis pub/sub

## Testing Locally

```bash
# Start Redis (if not running)
docker run -d -p 6379:6379 redis:latest

# Start the API
poetry run uvicorn pecha_api.app:api --reload

# Connect with wscat (npm install -g wscat)
wscat -c "ws://localhost:8000/api/v1/author/groups/{group_id}/posts/{post_id}/comments/live?token={token}"

# Send a comment
{"type": "comment", "text": "Hello!"}
```

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Connection refused | Server not running | Start the API server |
| 401 Unauthorized | Invalid/expired token | Check auth token validity |
| 404 Not Found | Group/post doesn't exist | Verify group is public, post is published |
| Message not received | WebSocket closed | Reconnect and resend |
| High latency | Network congestion | Check Redis connection, server load |
