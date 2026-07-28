# Quick Start: Posts Viewer Page

The interactive viewer page lets you test group posts and real-time comments in the browser with **built-in login**.

## TL;DR

```
http://localhost:8000/api/v1/view/groups/{group_id}/posts/{post_id}
```

Replace:
- `{group_id}` — UUID of your group
- `{post_id}` — UUID of your post

Then:
1. Enter your **email and password** in the login form
2. Click **Sign In**
3. Start commenting in real-time!

## What you get

- 🔐 **Built-in login** — No need to copy-paste tokens
- 🟢 **Live status indicator** — Shows when connected to WebSocket
- 💬 **Real-time comments** — Posts from other users appear instantly
- ⌨️ **Comment form** — Type and send comments directly
- 📱 **Responsive design** — Works on mobile and desktop
- 🔄 **Auto-reconnect** — Reconnects if connection drops
- 🚪 **Logout button** — Switch accounts anytime

## Example

Open viewer page for a specific post:

```
http://localhost:8000/api/v1/view/groups/550e8400-e29b-41d4-a716-446655440000/posts/550e8400-e29b-41d4-a716-446655440001
```

The page will show a login form where you enter your credentials.

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

**Login fails?**
- Check email and password are correct
- Verify user account exists in the system

**Won't connect after login?**
- Check Redis is running
- Check group is public, post is published

**No comments showing?**
- Verify post status is PUBLISHED  
- Check you're in a public group

**Can't type in textbox?**
- Wait for green status dot (connected)
- Make sure login was successful

**Getting "Connection refused"?**
- Make sure the FastAPI server is running
- Check Redis is running on port 6379

See [posts-viewer-page.md](posts-viewer-page.md) for detailed documentation.
