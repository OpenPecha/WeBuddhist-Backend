# Public author group DTO reference

Integration reference for the **public author group** surface: fetching a single group's public profile and following / unfollowing it.

Covers three endpoints:

| Method | Path | Auth | Response |
|--------|------|------|----------|
| `GET` | `/author/groups/{group_id}` | Public (none) | `AuthorGroupDetailDTO` (`200`) |
| `POST` | `/author/groups/{group_id}/follow` | Bearer | `204 No Content` |
| `DELETE` | `/author/groups/{group_id}/follow` | Bearer | `204 No Content` |

All paths are under the API root prefix `/api/v1`. `{group_id}` is a **UUID** (not the slug).

Aligned with code under `pecha_api/plans/groups/` (June 2026):

| File | Role |
|------|------|
| `groups_views.py` | Routers `public_groups_router` (`/author/groups`), `user_groups_router` (`/users/me/following/author/groups`) |
| `groups_service.py` | `get_author_group_detail`, `follow_group`, `unfollow_group`, DTO mappers |
| `groups_repository.py` | `get_group_by_id`, `upsert_group_follow`, `remove_group_follow`, `get_followers_count_map` |
| `groups_response_models.py` | `AuthorGroupDetailDTO` and nested DTOs |
| `groups_models.py` | `AuthorGroup`, `author_group_followers` join table |

---

## 1. `GET /author/groups/{group_id}`

Returns the **public profile** of one author group. No authentication required.

### Behavior

- Loads the group by UUID with metadata, members, social links, tags, series, and plans eagerly loaded.
- Returns `404 Not Found` (`detail: "Author group not found"`) if the group does not exist **or** if `is_public` is `false`. Private groups are indistinguishable from missing ones on this surface.
- `follower_count` is computed live from the `author_group_followers` table.

### Response: `AuthorGroupDetailDTO`

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | `UUID` | yes | Group ID |
| `slug` | `str` | yes | URL-friendly handle. No public lookup-by-slug route exists yet; use `id` |
| `is_public` | `bool` | yes | Always `true` on this endpoint (private → `404`) |
| `avatar_key` | `str` | no | Raw S3 key for the avatar |
| `banner_key` | `str` | no | Raw S3 key for the banner |
| `avatar_url` | `str` | no | Presigned avatar URL; `null` when no `avatar_key` |
| `banner_url` | `str` | no | Presigned banner URL; `null` when no `banner_key` |
| `metadata` | `GroupMetadataDTO[]` | yes | Per-language title + description; sorted by language |
| `members` | `AuthorGroupMemberDTO[]` | yes | Default `[]` |
| `tags` | `TagSummaryDTO[]` | yes | Default `[]` |
| `social_links` | `GroupSocialLinkDTO[]` | yes | Default `[]` |
| `series` | `SeriesListItemDTO[]` | yes | Group's series; default `[]` |
| `plans` | `PlanDTO[]` | yes | Group's plans; default `[]` |
| `follower_count` | `int` | yes | Live count of followers |

> **Image convention:** group avatar/banner use **single presigned URL strings** (`avatar_url`, `banner_url`), not the `ImageUrlModel` (`thumbnail`/`medium`/`original`) shape used for plan/series covers. Nested `series[].image` and `plans[].image_url` follow their own module conventions (see below).

> **No `is_following` flag.** This endpoint does not indicate whether the current user follows the group. To resolve follow state, cross-reference `GET /users/me/following/author/groups`.

### Nested: `GroupMetadataDTO`

The display name and description live here, one entry per language.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | `UUID` | yes | Metadata row ID |
| `title` | `str` | yes | Group display name for this language |
| `description` | `str` | no | |
| `language` | `str` | yes | `EN`, `BO`, `ZH` |

### Nested: `AuthorGroupMemberDTO`

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `author_id` | `UUID` | yes | |
| `role` | `str` | yes | `OWNER`, `ADMIN`, `AUTHOR`, `VIEWER` |
| `firstname` | `str` | yes | |
| `lastname` | `str` | yes | |
| `email` | `str` | yes | |

### Nested: `GroupSocialLinkDTO` (the "links")

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | `UUID` | yes | |
| `platform` | `str` | yes | Free-form platform label, e.g. `website`, `youtube`, `x` |
| `url` | `str` | yes | Link URL |

### Nested: `TagSummaryDTO`

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | `UUID` | yes | |
| `name` | `str` | yes | |
| `image` | `str` | no | Single URL string |
| `image_key` | `str` | no | Raw S3 key |
| `description` | `str` | no | |
| `featured` | `bool` | yes | Default `false` |

### Nested: `SeriesListItemDTO`

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | `UUID` | yes | |
| `metadata` | `SeriesMetadataDTO[]` | yes | `{ id, title, description, language }`; default `[]` |
| `image` | `ImageUrlModel` | no | `{ thumbnail, medium, original }` |
| `image_key` | `str` | no | Raw S3 key |
| `author_id` | `UUID` | yes | |
| `featured` | `bool` | yes | |
| `status` | `PlanStatus` | yes | `DRAFT`, `PUBLISHED`, `UNPUBLISHED`, `ARCHIVED`, `DELETED` |
| `plan_count` | `int` | yes | Active plans in the series; default `0` |
| `total_days` | `int` | yes | Default `0` |

### Nested: `PlanDTO`

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | `UUID` | yes | |
| `title` | `str` | yes | |
| `description` | `str` | yes | |
| `language` | `str` | yes | `EN`, `BO`, `ZH` |
| `difficulty_level` | `str` | no | `BEGINNER`, `INTERMEDIATE`, `ADVANCED` |
| `image_url` | `str` | no | Presigned URL string |
| `image_key` | `str` | no | Raw S3 key |
| `total_days` | `int` | yes | |
| `tags` | `TagSummaryDTO[]` | yes | Default `[]` |
| `status` | `PlanStatus` | yes | |
| `featured` | `bool` | no | Default `false` |
| `subscription_count` | `int` | yes | |
| `author` | `AuthorDTO` | no | `{ id, firstname, lastname, image_url, image_key }` |
| `start_date` | `datetime` | no | |
| `series_id` | `UUID` | no | |
| `display_order` | `int` | no | |
| `group_id` | `UUID` | no | This group's ID |

### Example response

```json
{
  "id": "8f1c9d2a-4b6e-4f3a-9c1d-2e7b5a0f1234",
  "slug": "dharma-collective",
  "is_public": true,
  "avatar_key": "images/group_images/.../avatar.webp",
  "banner_key": "images/group_images/.../banner.webp",
  "avatar_url": "https://bucket.s3.amazonaws.com/images/group_images/.../avatar.webp?...",
  "banner_url": "https://bucket.s3.amazonaws.com/images/group_images/.../banner.webp?...",
  "metadata": [
    { "id": "1f...", "title": "Dharma Collective", "description": "A community of translators.", "language": "EN" },
    { "id": "2a...", "title": "ཆོས་ཚོགས།", "description": null, "language": "BO" }
  ],
  "members": [
    { "author_id": "aa...", "role": "OWNER", "firstname": "Tenzin", "lastname": "Kunsang", "email": "tenzin@example.com" }
  ],
  "tags": [
    { "id": "t1...", "name": "Translation", "image": null, "image_key": null, "description": null, "featured": false }
  ],
  "social_links": [
    { "id": "s1...", "platform": "website", "url": "https://dharma.example.com" },
    { "id": "s2...", "platform": "youtube", "url": "https://youtube.com/@dharma" }
  ],
  "series": [
    {
      "id": "se...",
      "metadata": [{ "id": "m1...", "title": "Foundations", "description": "...", "language": "EN" }],
      "image": { "thumbnail": "https://...", "medium": "https://...", "original": "https://..." },
      "image_key": "images/series_images/.../original/cover.jpg",
      "author_id": "aa...",
      "featured": true,
      "status": "PUBLISHED",
      "plan_count": 3,
      "total_days": 21
    }
  ],
  "plans": [
    {
      "id": "pl...",
      "title": "Week 1",
      "description": "Intro practice",
      "language": "EN",
      "difficulty_level": "BEGINNER",
      "image_url": "https://bucket.s3.amazonaws.com/images/plan_images/.../cover.jpg?...",
      "image_key": "images/plan_images/.../original/cover.jpg",
      "total_days": 7,
      "tags": [],
      "status": "PUBLISHED",
      "featured": false,
      "subscription_count": 42,
      "author": { "id": "aa...", "firstname": "Tenzin", "lastname": "Kunsang", "image_url": null, "image_key": null },
      "start_date": null,
      "series_id": "se...",
      "display_order": 1,
      "group_id": "8f1c9d2a-4b6e-4f3a-9c1d-2e7b5a0f1234"
    }
  ],
  "follower_count": 128
}
```

### Errors

| Status | When |
|--------|------|
| `404` | Group not found, or group exists but `is_public` is `false` |

---

## 2. `POST /author/groups/{group_id}/follow`

Authenticated user follows a public group. Returns `204 No Content` (empty body).

### Request

- **Auth:** `Authorization: Bearer <token>` (required).
- **Path:** `group_id` (UUID).
- **Body:** none.

### Behavior

- Resolves the user from the token.
- Loads the group; returns `404` if it does not exist **or** `is_public` is `false`.
- **Idempotent:** inserting a follow that already exists is a no-op — no duplicate row, still `204`.
- Writes a row `(group_id, user_id, created_at)` into `author_group_followers`.

### Errors

| Status | When |
|--------|------|
| `401` | Missing / invalid bearer token |
| `404` | Group not found or not public |

```
POST /api/v1/author/groups/8f1c9d2a-4b6e-4f3a-9c1d-2e7b5a0f1234/follow
Authorization: Bearer eyJ...
→ 204 No Content
```

---

## 3. `DELETE /author/groups/{group_id}/follow`

Authenticated user unfollows a group. Returns `204 No Content` (empty body).

### Request

- **Auth:** `Authorization: Bearer <token>` (required).
- **Path:** `group_id` (UUID).
- **Body:** none.

### Behavior

- Resolves the user from the token.
- Deletes the matching `(group_id, user_id)` row from `author_group_followers`.
- **Idempotent and unconditional:** unfollowing when not following still returns `204`. Unlike follow, this does **not** verify the group exists or is public first — it simply deletes any matching row.

### Errors

| Status | When |
|--------|------|
| `401` | Missing / invalid bearer token |

```
DELETE /api/v1/author/groups/8f1c9d2a-4b6e-4f3a-9c1d-2e7b5a0f1234/follow
Authorization: Bearer eyJ...
→ 204 No Content
```

---

## Resolving follow state (related endpoint)

Because the detail response has no `is_following` flag, list the user's followed groups and check membership client-side:

`GET /api/v1/users/me/following/author/groups` (Bearer) → `AuthorGroupListResponse`

| Field | Type | Notes |
|-------|------|-------|
| `groups` | `AuthorGroupSummaryDTO[]` | Followed groups (paginated) |
| `skip` | `int` | Query param, default `0` |
| `limit` | `int` | Query param, default `20`, range `1..100` |
| `total` | `int` | Total followed groups |

**`AuthorGroupSummaryDTO`** (lighter than detail — no images, members, links, series, or plans):

| Field | Type | Notes |
|-------|------|-------|
| `id` | `UUID` | |
| `slug` | `str` | |
| `is_public` | `bool` | |
| `metadata` | `GroupMetadataDTO[]` | |
| `tags` | `TagSummaryDTO[]` | Default `[]` |
| `follower_count` | `int` | Default `0` |
| `member_count` | `int` | Default `0` |

A group `id` present in this list means the current user follows it.

---

## Integration notes

- **Lookup is by UUID, not slug.** `slug` is returned for display/routing, but there is no `GET /author/groups/by-slug/{slug}` route. Always call detail/follow with the `group_id` UUID.
- **Follow/unfollow are fire-and-forget `204`s.** No response body; update local UI optimistically and reconcile via the followed-groups list.
- **Follower count is eventually consistent in the UI.** `follower_count` on detail reflects the DB at fetch time; after follow/unfollow, refetch detail (or adjust locally) to update the displayed count.
- **Private groups 404 on the public detail route.** Only `is_public` groups are reachable here.
