# FCM Notification Types

This document lists every notification the backend produces for delivery to
the app via FCM, what triggers it, how the worker fetches it, the exact
title/body shape for each, and the exact FCM wire payload the worker sends.

The `notification`/`data` payload shapes below come from the worker's
[`fcm_client.py`](../../../WeBuddhist-worker/worker_api/notifications/services/push/fcm_client.py)
— it constructs and sends every FCM message, forwarding the title/body/image
resolved by this backend's internal endpoints unchanged.

## `notification_type` / `session_type` summary

| Notification | `notification_type` | `session_type` |
|---|---|---|
| Chat message | `CHAT_MESSAGE` | `CHAT` |
| Group post | `GROUP_POST` | `GROUP_POST` |
| Event | `EVENT` | `EVENT` |
| Join request created | `JOIN_REQUEST_CREATED` | `GROUP` |
| Join request decided | `JOIN_REQUEST_DECIDED` | `GROUP` |
| Verse of the day | `VERSE_OF_DAY` | `VERSE_OF_DAY` |
| Routine (plan/series) | *(not set)* ⚠️ | `PLAN` or `SERIES` |

Routine notifications are the only type that doesn't set `notification_type`
in the data payload — everything else sets both fields.

## How delivery works

The backend never calls FCM directly. For each notification type it either:

- **Enqueues an SQS event** (chat, group post, event, join request) containing
  only an ID. A worker (WeBuddhist-worker) consumes the event, calls an
  internal `GET /api/v1/internal/...` endpoint on this backend to resolve the
  title/body and recipient device tokens, then sends the FCM messages and
  deactivates permanently invalid tokens.
- **Is polled by the worker on a schedule** (verse of the day, routine
  reminders). The worker calls an internal endpoint every minute; the backend
  returns targets only for users whose local time/timezone currently matches.

All internal endpoints require the `X-Dispatch-Token` header
(`NOTIFICATION_DISPATCH_SECRET_TOKEN`).

---

## 1. Chat message

**Trigger:** A direct or group chat message is sent (REST or WebSocket).
**SQS event:** `CHAT_MESSAGE_CREATED` → `CHAT_NOTIFICATION_SQS_QUEUE_URL`
**Internal endpoint:** `GET /internal/chat-notification-targets/{message_id}`
**Source:** [notification_service.py](../../pecha_api/chat/notification_service.py)

| Chat kind | Title | Body |
|-----------|-------|------|
| Private   | Sender's display name | Message preview (truncated to `CHAT_NOTIFICATION_PREVIEW_MAX_LENGTH`, default 120 chars, `…` suffix) |
| Group     | Room name | `"{sender_name}: {message preview}"` |

**Recipients:** the other participant (private) or all group members except
the sender (group), limited to users with active push devices.

**FCM payload:**
```json
{
  "notification": { "title": "...", "body": "..." },
  "data": {
    "notification_type": "CHAT_MESSAGE",
    "session_type": "CHAT",
    "chat_kind": "PRIVATE | GROUP",
    "room_id": "<uuid>",
    "message_id": "<uuid>",
    "sender_id": "<uuid>",
    "group_id": "<uuid or \"\">",
    "source_id": "<room_id>",
    "title": "...",
    "body": "...",
    "image_url": ""
  }
}
```

---

## 2. Group post created

**Trigger:** A group post is published.
**SQS event:** `GROUP_POST_CREATED` → `GROUP_POST_NOTIFICATION_SQS_QUEUE_URL`
**Internal endpoint:** `GET /internal/group-post-notification-targets/{post_id}`
**Source:** [notification_service.py](../../pecha_api/group_posts/notification_service.py)

| Field | Value |
|-------|-------|
| Title | Group's display title (English metadata, else first available, else group slug, else `"Group"`) |
| Body  | Post caption, truncated to `GROUP_POST_NOTIFICATION_PREVIEW_MAX_LENGTH` (default 120). If the post has no caption: `"New post"` |

If the post is not `PUBLISHED`, the endpoint returns an empty title/body and
no recipients (no-op notification).

**Recipients:** group members except the post author, with active push devices.

**FCM payload:**
```json
{
  "notification": { "title": "...", "body": "..." },
  "data": {
    "notification_type": "GROUP_POST",
    "session_type": "GROUP_POST",
    "post_id": "<uuid>",
    "group_id": "<uuid>",
    "author_id": "<uuid>",
    "source_id": "<post_id>",
    "title": "...",
    "body": "...",
    "image_url": ""
  }
}
```

---

## 3. Event created

**Trigger:** A group event is created.
**SQS event:** `EVENT_CREATED` → `EVENT_NOTIFICATION_SQS_QUEUE_URL`
**Internal endpoint:** `GET /internal/event-notification-targets/{event_id}`
**Source:** [notification_service.py](../../pecha_api/events/notification_service.py)

| Field | Value |
|-------|-------|
| Title | Group's display title (same resolution as group posts) |
| Body  | Event name (English metadata, else first available, else `"New event"`), truncated to `EVENT_NOTIFICATION_PREVIEW_MAX_LENGTH` (default 120) |

**Recipients:** group members except the event creator, with active push devices.

**FCM payload:**
```json
{
  "notification": { "title": "...", "body": "..." },
  "data": {
    "notification_type": "EVENT",
    "session_type": "EVENT",
    "event_id": "<uuid>",
    "group_id": "<uuid>",
    "author_id": "<uuid>",
    "source_id": "<event_id>",
    "title": "...",
    "body": "...",
    "image_url": ""
  }
}
```

---

## 4. Group join request

**Trigger:** A user requests to join a group, or a moderator approves/declines
the request.
**SQS events:** `JOIN_REQUEST_CREATED` / `JOIN_REQUEST_DECIDED` →
`JOIN_REQUEST_NOTIFICATION_SQS_QUEUE_URL`
**Internal endpoint:** `GET /internal/join-request-notification-targets/{join_request_id}?event_type=...`
**Source:** [join_request_notification_service.py](../../pecha_api/plans/groups/join_request_notification_service.py)

| Event | Title | Body | Recipients |
|-------|-------|------|------------|
| `JOIN_REQUEST_CREATED` | `"Request to join {group_name}"` | `"{requester_name} asked to join {group_name}."` | Group owners/admins (Studio authors mapped to app users by email) |
| Decided → approved | `"You've joined {group_name}"` | `"Your request to join {group_name} was approved."` | The requester |
| Decided → declined | `"Request to join {group_name} declined"` | `"Your request to join {group_name} was not approved."` | The requester |

**FCM payload:**
```json
{
  "notification": { "title": "...", "body": "..." },
  "data": {
    "notification_type": "JOIN_REQUEST_CREATED | JOIN_REQUEST_DECIDED",
    "session_type": "GROUP",
    "join_request_id": "<uuid>",
    "group_id": "<uuid>",
    "status": "PENDING | APPROVED | REJECTED",
    "source_id": "<group_id>",
    "title": "...",
    "body": "...",
    "image_url": ""
  }
}
```

---

## 5. Verse of the day

**Trigger:** Scheduled — worker polls every minute; backend returns a target
only for users whose local time is 10:00 AM in their stored timezone.
**Internal endpoint:** `GET /internal/verse-of-day-notification-targets`
**Source:** [verse_of_day_notification_service.py](../../pecha_api/verse_of_day/verse_of_day_notification_service.py)

| Field | Value |
|-------|-------|
| Title | `VERSE_OF_DAY_NOTIFICATION_TITLE` config value, default `"Verse of the Day"` |
| Body  | That day's verse text in the user's preferred language (falls back to English) |
| Image | Verse-of-day image URL, if one is published |

Users are skipped (no notification) if no verse is published for their local
date, or no text exists in their language or the English fallback.

**FCM payload:**
```json
{
  "notification": { "title": "...", "body": "...", "image": "<url or omitted>" },
  "data": {
    "notification_type": "VERSE_OF_DAY",
    "session_type": "VERSE_OF_DAY",
    "title": "...",
    "body": "...",
    "image_url": "<url or \"\">"
  }
}
```

---

## 6. Routine reminder (plan / series)

**Trigger:** Scheduled — worker polls every minute; backend returns targets
for users whose routine time-block matches the current UTC time (`HH:MM`).
**Internal endpoints:**
- `GET /internal/routine-notification-targets`
- `GET /internal/plan-notification-content?user_id=...&plan_id=...`

**Source:** [routine_notification_service.py](../../pecha_api/routines/routine_notifications/routine_notification_service.py)

Content resolution depends on the session type behind the routine time-block:

| Session type | Title | Body | Image |
|--------------|-------|------|-------|
| `PLAN`, with a day-specific notification configured | That day's custom title | That day's custom body | Custom image if set, else the plan's image |
| `PLAN`, no day-specific notification | Plan title | `NOTIFICATION_DEFAULT_BODY` | Plan's image |
| `SERIES` | Series title (English metadata) | `NOTIFICATION_DEFAULT_BODY` | Series image |
| Unknown / no source | `NOTIFICATION_DEFAULT_TITLE` | `NOTIFICATION_DEFAULT_BODY` | — |

Defaults (`pecha_api/config.py`):
- `NOTIFICATION_DEFAULT_TITLE = "WebBuddhist"`
- `NOTIFICATION_DEFAULT_BODY = "Time for your daily practice."`

A user's current plan "day number" is computed from when they started the
plan relative to today (UTC), which determines which day's custom
title/body/image (if any) is used.

**FCM payload:**
```json
{
  "notification": { "title": "...", "body": "...", "image": "<url or omitted>" },
  "data": {
    "session_type": "PLAN | SERIES",
    "source_id": "<plan_id | series_id | \"\">",
    "title": "...",
    "body": "...",
    "image_url": "<url or \"\">"
  }
}
```
⚠️ No `notification_type` key — inconsistent with every other notification type.

---

## Config reference

| Variable | Default | Used by |
|----------|---------|---------|
| `CHAT_NOTIFICATION_PREVIEW_MAX_LENGTH` | 120 | Chat |
| `GROUP_POST_NOTIFICATION_PREVIEW_MAX_LENGTH` | 120 | Group post |
| `EVENT_NOTIFICATION_PREVIEW_MAX_LENGTH` | 120 | Event |
| `VERSE_OF_DAY_NOTIFICATION_TITLE` | `"Verse of the Day"` | Verse of the day |
| `NOTIFICATION_DEFAULT_TITLE` | `"WebBuddhist"` | Routine (fallback) |
| `NOTIFICATION_DEFAULT_BODY` | `"Time for your daily practice."` | Routine (fallback) |
| `NOTIFICATION_DISPATCH_SECRET_TOKEN` | — | Auth for all internal endpoints above |
