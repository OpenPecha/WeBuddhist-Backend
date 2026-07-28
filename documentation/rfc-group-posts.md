# RFC: Group Posts (Instagram-style)

| Field | Value |
|-------|-------|
| **Status** | Proposed |
| **Date** | 2026-07-27 |
| **Scope** | WeBuddhist-Backend |
| **Related** | Author Groups (`/cms/author/groups`, `/author/groups`), Events (`event_links`), CMS Media (`/cms/media`) |

---

## 1. Summary

Add **group-owned social posts**: Instagram-style feed items on an **Author Group** with caption text, ordered media (image/video/audio), and external links.

CMS/Studio authors create and manage posts; the public app reads a chronological feed under `/author/groups`.

---

## 2. Motivation

| Today | Gap |
|-------|-----|
| Groups have plans, series, events, accumulators, recitations | No free-form social feed |
| Share module only covers text/segment OG links | Groups cannot publish captions + media + links |
| Studio manages group content via CMS | No CMS APIs for posts |

Product need: PAGE and COMMUNITY groups can publish posts (text, media, links) for followers/joiners.

---

## 3. Goals

- Persist group-scoped posts, media, and links in Postgres.
- CMS: create / list / update / soft-delete posts; attach ordered media and links.
- Public: paginated feed + post detail under `/author/groups/{group_id}/posts`.
- Reuse S3 upload + presign patterns and existing group permission helpers.

## 4. Non-goals (v1)

- Likes, comments, shares, or reactions.
- Member-authored posts (joined users posting) — CMS authors only in v1.
- Cross-group / home timeline (“posts from groups I follow”).
- Stories, reels, or live.
- Draft/schedule workflow beyond `PUBLISHED` / `HIDDEN` status.
- Multilingual caption metadata (single caption string).

---

## 5. Data model

### 5.1 Enums

```text
group_post_status:     PUBLISHED | HIDDEN
group_post_media_type: IMAGE | VIDEO | AUDIO
```

### 5.2 `group_posts`

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | `uuid4` |
| `group_id` | UUID FK → `author_groups.id` ON DELETE CASCADE | Owner |
| `caption` | TEXT NULL | Instagram-style body text |
| `status` | ENUM `group_post_status` NOT NULL | Default `PUBLISHED` |
| `published_at` | TIMESTAMPTZ NOT NULL | Feed sort key (set on create; editable) |
| `created_at` | TIMESTAMPTZ NOT NULL | |
| `updated_at` | TIMESTAMPTZ NOT NULL | |
| `deleted_at` | TIMESTAMPTZ NULL | Soft delete |
| `created_by` | VARCHAR(255) NOT NULL | CMS author email |
| `updated_by` | VARCHAR(255) NULL | |

**Indexes**

- `idx_group_posts_group_id` on `group_id`
- `idx_group_posts_feed` on `(group_id, published_at DESC)` WHERE `deleted_at IS NULL AND status = 'PUBLISHED'`

### 5.3 `group_post_media`

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `post_id` | UUID FK → `group_posts.id` ON DELETE CASCADE | |
| `media_type` | ENUM `group_post_media_type` NOT NULL | `IMAGE`, `VIDEO`, or `AUDIO` |
| `media_key` | VARCHAR(1000) NOT NULL | S3 key; presign on read |
| `thumbnail_key` | VARCHAR(1000) NULL | Optional video poster / image thumb / audio cover |
| `width` | INTEGER NULL | Image/video only |
| `height` | INTEGER NULL | Image/video only |
| `duration_ms` | INTEGER NULL | Video/audio only |
| `display_order` | INTEGER NOT NULL | 1-based carousel order |
| `created_at` | TIMESTAMPTZ NOT NULL | |

**Constraints**

- Index on `post_id`
- `UNIQUE (post_id, display_order)`
- v1 limit (app-enforced): max **10** media items per post

### 5.4 `group_post_links`

Same shape as `event_links`:

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `post_id` | UUID FK → `group_posts.id` ON DELETE CASCADE | |
| `type` | VARCHAR(50) NOT NULL | e.g. `EXTERNAL`, `YOUTUBE`, `WEBSITE` |
| `url` | VARCHAR(2000) NOT NULL | |
| `label` | VARCHAR(255) NULL | |
| `display_order` | INTEGER NOT NULL | Default `1` |
| `created_at` | TIMESTAMPTZ NOT NULL | |
| `updated_at` | TIMESTAMPTZ NOT NULL | |

**Indexes:** `idx_group_post_links_post_id` on `post_id`

### 5.5 Validation rules

- A post must have **at least one** of: non-empty `caption`, ≥1 media, ≥1 link.
- Soft-deleted posts are omitted from public feed; CMS list may include them via query flag (optional; default exclude).
- `HIDDEN` posts are CMS-visible only; public returns 404.

### 5.6 Migration

One Alembic revision: enums + three tables + FKs + indexes.

---

## 6. Permissions

Reuse `pecha_api/plans/shared/permissions.py`:

| Action | Rule |
|--------|------|
| CMS list / detail | `require_can_read_group_content` (OWNER, ADMIN, AUTHOR, VIEWER) |
| CMS create / update / media / links | `require_can_create_content` (OWNER, ADMIN, AUTHOR) |
| CMS delete / hide | `require_can_change_status` (OWNER, ADMIN) |
| Public read | Group `deleted_at IS NULL`; private groups follow existing public-group rules; only `PUBLISHED` + not soft-deleted |

CMS routes: Bearer + CMS author validation.

---

## 7. API design

### 7.1 URL conventions

| Audience | Prefix | Precedent |
|----------|--------|-----------|
| CMS | `/cms/author/groups/{group_id}/posts` | group recitation-collections / accumulators |
| Public | `/author/groups/{group_id}/posts` | `/author/groups/{group_id}/...` |
| Media upload | `/cms/media/upload/group-post` | `/cms/media/upload/...` |

### 7.2 CMS endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/cms/author/groups/{group_id}/posts` | Create post (caption + media keys + links) |
| `GET` | `/cms/author/groups/{group_id}/posts` | List posts (`skip`, `limit`, optional `status`) |
| `GET` | `/cms/author/groups/{group_id}/posts/{post_id}` | Detail |
| `PATCH` | `/cms/author/groups/{group_id}/posts/{post_id}` | Update caption / status / `published_at` |
| `PUT` | `/cms/author/groups/{group_id}/posts/{post_id}/media` | Replace ordered media set |
| `PUT` | `/cms/author/groups/{group_id}/posts/{post_id}/links` | Replace ordered links (same pattern as group social-links) |
| `DELETE` | `/cms/author/groups/{group_id}/posts/{post_id}` | Soft-delete |
| `POST` | `/cms/media/upload/group-post` | Upload image/video/audio → returns `media_key` (+ optional thumb) |

### 7.3 Public endpoints

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/author/groups/{group_id}/posts` | Chronological feed (`skip`, `limit`) — `PUBLISHED` only |
| `GET` | `/author/groups/{group_id}/posts/{post_id}` | Post detail with presigned media URLs |

### 7.4 Request / response sketches

**Create**

```json
{
  "caption": "Evening practice notes 🙏",
  "status": "PUBLISHED",
  "published_at": null,
  "media": [
    { "media_type": "IMAGE", "media_key": "groups/.../posts/a.webp", "display_order": 1 }
  ],
  "links": [
    { "type": "EXTERNAL", "url": "https://example.com", "label": "Full guide", "display_order": 1 }
  ]
}
```

**List / detail item**

```json
{
  "id": "...",
  "group_id": "...",
  "caption": "...",
  "status": "PUBLISHED",
  "published_at": "2026-07-27T10:00:00Z",
  "media": [
    {
      "id": "...",
      "media_type": "IMAGE",
      "url": "https://presigned...",
      "thumbnail_url": null,
      "width": 1080,
      "height": 1350,
      "duration_ms": null,
      "display_order": 1
    }
  ],
  "links": [
    { "id": "...", "type": "EXTERNAL", "url": "https://example.com", "label": "Full guide", "display_order": 1 }
  ],
  "created_at": "...",
  "updated_at": "..."
}
```

List wrappers: `{ "posts": [...], "skip", "limit", "total" }` (match existing list response style).

---

## 8. Module layout

```text
pecha_api/group_posts/
  models.py
  enums.py
  repository.py
  service.py
  response_models.py
  views.py          # public
  cms_views.py      # CMS
```

Register both routers in `pecha_api/app.py`. Extend `pecha_api/plans/media/` for the group-post upload path.

---

## 9. Open questions

1. **Member posts (v2)?** Allow `COMMUNITY` joiners to author posts, or keep CMS-only?
2. **Media limits?** Max size / duration / codecs for `VIDEO` and `AUDIO` uploads.
3. **Notifications?** Notify followers/joiners on new `PUBLISHED` post?
4. **PAGE vs COMMUNITY?** Same post APIs for both, or COMMUNITY-only?

---

## 10. Implementation order

1. Alembic migration (`group_posts`, `group_post_media`, `group_post_links` + enums).
2. Models → repository → service → Pydantic DTOs.
3. CMS CRUD + media replace + links replace.
4. Media upload endpoint.
5. Public feed + detail.
6. Tests (permissions, soft-delete, HIDDEN visibility, empty-content validation).
