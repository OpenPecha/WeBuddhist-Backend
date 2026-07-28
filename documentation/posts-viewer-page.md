# Posts Viewer Page

The viewer page provides an interactive HTML interface to test group posts and real-time comments.

## Accessing the Viewer

```
http://localhost:8000/api/v1/view/groups/{group_id}/posts/{post_id}?token={auth_token}
```

## URL Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `group_id` | UUID | Yes | The author group ID |
| `post_id` | UUID | Yes | The post ID within that group |
| `token` | string | Yes | Bearer authentication token |

## Features

### Real-Time Comments
- Live comment stream using WebSocket
- Status indicator shows connection status (🟢 connected, 🔴 disconnected)
- Auto-reconnects if connection drops
- Messages arrive instantly as they're posted

### Comment Display
- Shows all comments in reverse chronological order (newest first)
- Displays commenter email, text, and timestamp
- HTML-escaped for security
- Character counter (0-5000)

### Post Comment
- Type comment in the textarea at the bottom
- Press **Send** button or **Ctrl+Enter** to submit
- Validation ensures 1-5000 characters
- Button is disabled when offline
- Your comment appears instantly in the stream

### Error Handling
- Connection errors display at top of comment list
- Validation errors (empty, too long) shown with context
- Auto-dismiss errors after 5 seconds

## Testing Guide

### 1. Get valid credentials

First, authenticate to get a token:

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password"
  }'

# Returns: { "access_token": "...", "token_type": "bearer" }
```

### 2. Create a test group post

```bash
GROUP_ID="550e8400-e29b-41d4-a716-446655440000"  # Use real group ID
TOKEN="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."  # Use token from step 1

curl -X POST http://localhost:8000/api/v1/cms/author/groups/$GROUP_ID/posts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "caption": "Test post",
    "status": "PUBLISHED"
  }'

# Returns: { "id": "550e8400...", ... }
POST_ID="550e8400-e29b-41d4-a716-446655440001"  # Use post ID from response
```

### 3. Open the viewer page

Open browser to:
```
http://localhost:8000/api/v1/view/groups/550e8400-e29b-41d4-a716-446655440000/posts/550e8400-e29b-41d4-a716-446655440001?token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

### 4. Test real-time comments

**In viewer page:**
- Type "Hello World" in the comment box
- Click Send or press Ctrl+Enter
- Comment appears instantly in the stream with current timestamp

**Open another browser tab (same viewer URL):**
- Second tab should show "🟢 Connected"
- Post a comment in first tab
- Second tab receives it in real-time without refreshing

### 5. Test disconnection/reconnection

**Disconnect test:**
- Stop Redis: `docker stop <redis-container>`
- Try posting a comment → Shows error
- Status indicator shows "🔴 Disconnected"

**Reconnect test:**
- Restart Redis: `docker start <redis-container>`
- Page auto-reconnects within 3 seconds
- Status shows "🟢 Connected"

## Browser Support

- ✅ Chrome/Edge 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Mobile browsers (responsive design)

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+Enter | Send comment |
| Tab | Focus next field |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Connecting..." forever | Check Redis is running, verify token is valid |
| Comments not appearing | Verify post status is PUBLISHED |
| 404 error | Check group_id and post_id are valid |
| Cannot type in textarea | Wait for "🟢 Connected" status |
| Comments don't update in real-time | Check browser supports WebSocket (all modern browsers do) |

## Example Testing Scenario

```bash
# 1. Get token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}' | jq -r '.access_token')

# 2. Create post
POST=$(curl -s -X POST http://localhost:8000/api/v1/cms/author/groups/GROUP_ID/posts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"caption":"Test","status":"PUBLISHED"}')

POST_ID=$(echo $POST | jq -r '.id')

# 3. Open viewer
echo "Visit: http://localhost:8000/api/v1/view/groups/GROUP_ID/posts/$POST_ID?token=$TOKEN"

# 4. Post a comment via API in another terminal
curl -s -X POST http://localhost:8000/api/v1/author/groups/GROUP_ID/posts/$POST_ID/comments \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text":"Posted via API"}' | jq .

# 5. Comment should appear in viewer instantly!
```
