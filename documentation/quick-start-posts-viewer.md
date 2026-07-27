# Quick Start: Posts Viewer Page

The interactive viewer page lets you test group posts and real-time comments in the browser.

## TL;DR

```
http://localhost:8000/api/v1/view/groups/{group_id}/posts/{post_id}?token={token}
```

Replace:
- `{group_id}` — UUID of your group
- `{post_id}` — UUID of your post  
- `{token}` — Your bearer auth token

## What you get

- 🟢 **Live status indicator** — Shows when connected to WebSocket
- 💬 **Real-time comments** — Posts from other users appear instantly
- ⌨️ **Comment form** — Type and send comments directly
- 📱 **Responsive design** — Works on mobile and desktop
- 🔄 **Auto-reconnect** — Reconnects if connection drops

## Example

Viewer page for a specific post:

```
http://localhost:8000/api/v1/view/groups/550e8400-e29b-41d4-a716-446655440000/posts/550e8400-e29b-41d4-a716-446655440001?token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

## How to test end-to-end

1. **Open viewer in two browser tabs** with the same post
2. **Type a comment** in one tab → Click Send
3. **Watch it appear** in the other tab instantly ✨
4. **No refresh needed** — Real-time WebSocket magic

## Keyboard shortcuts

- **Ctrl+Enter** → Send comment
- **Tab** → Navigate fields

## What it connects to

- **REST API** → Load initial comments (GET)
- **WebSocket** → Real-time comment stream (GET ws)
- **POST endpoint** → Submit comments if using REST fallback

## Browser requirements

- Modern browser with WebSocket support
- JavaScript enabled
- CORS enabled (should be automatic)

## Troubleshooting

**Won't connect?**
- Check Redis is running
- Verify token is valid
- Check group is public, post is published

**No comments showing?**
- Verify post status is PUBLISHED  
- Check you're in a public group

**Can't type in textbox?**
- Wait for green status dot (connected)
- Post may not have loaded yet

See [posts-viewer-page.md](posts-viewer-page.md) for detailed documentation.
