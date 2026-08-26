# Poems API

Short reference for the Poem feature: a simple content type (title, content, author, chapter, language) with a public read-only API and a CMS-authenticated write API.

All paths are relative to `/api/v1`.

## Data model

| Field | Type | Notes |
|---|---|---|
| `id` | UUID | |
| `title` | string | required |
| `content` | string | required |
| `author_name` | string | required |
| `chapter_name` | string? | optional grouping (e.g. book/collection name) |
| `language` | string | one of the platform's `LanguageCode` values (`EN`, `BO`, `ZH`, `HI`, `NE`, `MN`, `LA`). Defaults to `EN` |
| `image_url` | string? | presigned S3 URL, read-only |
| `image_key` | string? | S3 key, write-only (CMS) |
| `status` | `DRAFT` \| `PUBLISHED` | defaults to `DRAFT` |
| `published_at` | datetime? | set automatically when status becomes `PUBLISHED` |
| `created_at` / `updated_at` | datetime | |

Deleting is a soft delete (`deleted_at`) — rows are hidden, not removed.

---

## Public endpoints (`/poems`) — no auth

Only returns poems with `status = PUBLISHED`.

| Method | Path | Description |
|---|---|---|
| GET | `/poems` | List published poems, newest first. Query: `skip`, `limit` (1-100, default 20), `chapter_name`, `author_name` (exact match filters), `language` (filter by language code) |
| GET | `/poems/{poem_id}` | Get one published poem. 404 if missing or not published |

## CMS endpoints (`/cms/poems`) — Bearer token, CMS author required

| Method | Path | Description |
|---|---|---|
| GET | `/cms/poems` | List poems of any status. Query: `skip`, `limit`, `status`, `chapter_name`, `author_name`, `language` |
| GET | `/cms/poems/{poem_id}` | Get any poem by id, regardless of status |
| POST | `/cms/poems` | Create a poem. Body: `title`, `content`, `author_name`, `chapter_name?`, `language?` (default `EN`), `image_key?`, `status?` (default `DRAFT`) → `201` |
| PATCH | `/cms/poems/{poem_id}` | Partial update — same fields as create, all optional. Setting `status: PUBLISHED` stamps `published_at` |
| DELETE | `/cms/poems/{poem_id}` | Soft delete → `204` |

**Image upload**: upload the file via `POST /cms/media/upload` (multipart, returns `{ key, image: { original, ... } }`), then pass the returned `key` as `image_key` on create/update.

**Errors**: `404` poem not found, `422` validation (empty `title`/`content`/`author_name`, or invalid `language`/`status` value).

---

## Studio (CMS UI)

Poems can be created/edited/deleted from the Studio at `/poems` (Poems nav item), which calls the CMS endpoints above. The create/edit form includes a language selector, and the list page supports filtering by language.
